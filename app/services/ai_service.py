import json
import re
import uuid as _uuid
import logging

from openai import OpenAI, APITimeoutError, APIError
from sqlalchemy.orm import Session as DBSession, joinedload
from fastapi import HTTPException

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.db import SessionLocal
from app.models.session import Session
from app.models.question import Question
from app.schemas.ai import AIQuestion, AIQuestionsResponse, AIResult, AIResultsResponse
from app.schemas.question import QuestionOut, QuestionOptionOut
from app.constants import AI_MAX_QUESTIONS, AI_MIN_QUESTIONS, Mechanic, AI_TIMEOUT_SECONDS, AI_MAX_RETRIES, SessionState, ResultType
from app.services.event_manager import event_manager
from app.utils.prompts import ANSWER_SUMMARY_GENERATION_SYSTEM_PROMPT, RESULT_GENERATION_SYSTEM_PROMPT, QUESTION_GENERATION_SYSTEM_PROMPT
from app.utils.http import HTTPStatusCode, HTTPErrorMessage
from app.services.question_service import QuestionService
from app.services.result_service import ResultService
from app.services.answer_service import AnswerService
from app.services.pendo_service import pendo_track

logger = logging.getLogger(__name__)

_openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=AI_TIMEOUT_SECONDS,
)

class AIService:
    @staticmethod
    def generate_questions(
        session_id: str,
        topic: str,
        context: str | None,
    ) -> bool:
        logger.info("Starting question generation for session %s", session_id)
        user_prompt = AIService._build_user_prompt(topic, context)
        total_attempts = AI_MAX_RETRIES + 1

        for attempt in range(1, total_attempts + 1):
            try:
                logger.info("Session %s: question generation attempt %d/%d", session_id, attempt, total_attempts)
                result_response = AIService._generate_questions_response(_openai_client, user_prompt)
                if result_response is None:
                    logger.warning("Session %s: received null response from OpenAI", session_id)
                    return False

                if not result_response.valid:
                    logger.warning("Session %s: response marked as invalid by AI", session_id)
                    return False

                if AIService._validate_response(result_response.questions):
                    logger.info("Session %s: validation passed with %d questions, saving", session_id, len(result_response.questions))
                    db = SessionLocal()
                    try:
                        QuestionService.save_questions(db, session_id, result_response.questions)
                    finally:
                        db.close()

                    mechanic_counts = {}
                    for q in result_response.questions:
                        m = q.mechanic.value if hasattr(q.mechanic, "value") else str(q.mechanic)
                        mechanic_counts[m] = mechanic_counts.get(m, 0) + 1

                    pendo_track(
                        "questions_generated",
                        visitor_id="system",
                        account_id=session_id,
                        properties={
                            "session_id": session_id,
                            "question_count": len(result_response.questions),
                            "attempt_number": attempt,
                            "mechanic_distribution": json.dumps(mechanic_counts),
                        },
                    )
                    return True
                else:
                    logger.warning("Session %s: validation failed for %d questions", session_id, len(result_response.questions))

            except APITimeoutError:
                logger.warning("Session %s: OpenAI timeout on attempt %d", session_id, attempt)
                continue

            except (APIError, Exception):
                logger.exception("Question generation failed for session %s on attempt %d", session_id, attempt)
                return False

        logger.error("Session %s: question generation exhausted all %d attempts", session_id, total_attempts)
        return False

    @staticmethod
    def get_questions(
        db: DBSession,
        session_id: str,
    ) -> list[QuestionOut]:
        session = db.query(Session).filter(
            Session.id == _uuid.UUID(session_id)
        ).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )

        questions = (
            db.query(Question)
            .options(joinedload(Question.options))
            .filter(Question.session_id == _uuid.UUID(session_id))
            .order_by(Question.display_order)
            .all()
        )

        if not questions:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.QUESTIONS_NOT_READY,
            )

        return [
            QuestionOut(
                id=str(q.id),
                text=q.text,
                mechanic=q.mechanic,
                display_order=q.display_order,
                options=[
                    QuestionOptionOut(id=str(o.id), label=o.label, display_order=o.display_order)
                    for o in q.options
                ],
            )
            for q in questions
        ]

    @staticmethod
    def _generate_questions_response(client: OpenAI, user_prompt: str) -> AIQuestionsResponse | None:
        try:
            completion = client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": QUESTION_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=AIQuestionsResponse,
            )
            result = completion.choices[0].message.parsed
            return result if result else None
        except APIError:
            return None

    @staticmethod
    def generate_results(session_id: str) -> None:
        logger.info("Starting result generation for session %s", session_id)
        total_attempts = AI_MAX_RETRIES + 1
        succeeded = False

        try:
            for attempt in range(1, total_attempts + 1):
                try:
                    logger.info("Session %s: result generation attempt %d/%d", session_id, attempt, total_attempts)
                    answers_data = AnswerService.fetch_session_answers(session_id)
                    if not answers_data:
                        logger.warning("Session %s: no answers found, aborting result generation", session_id)
                        return

                    logger.info("Session %s: generating answer summary", session_id)
                    answer_summary = AIService._generate_answer_summary(_openai_client, answers_data)
                    if not answer_summary:
                        logger.warning("Session %s: answer summary generation failed, retrying", session_id)
                        continue

                    overall_result = AIService._extract_overall_result(answer_summary)
                    if not overall_result:
                        logger.warning("Session %s: OVERALL extraction failed, retrying", session_id)
                        continue

                    logger.info("Session %s: generating result response", session_id)
                    results_response = AIService._generate_result_response(
                        _openai_client, answer_summary, answers_data, overall_result
                    )

                    if results_response is None or not results_response.valid:
                        logger.warning("Session %s: result response null or invalid, retrying", session_id)
                        continue

                    if AIService._validate_results(results_response.results):
                        all_results = [overall_result] + results_response.results
                        logger.info("Session %s: validation passed with %d results (%d recommendations), saving", session_id, len(all_results), len(results_response.results))
                        db = SessionLocal()
                        try:
                            ResultService.save_results(db, session_id, all_results)
                            session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
                            if session:
                                session.state = SessionState.RESULTS
                                db.commit()
                                succeeded = True
                                event_manager.publish(session_id, SessionState.RESULTS.value)
                        finally:
                            db.close()

                        pendo_track(
                            "results_generated",
                            visitor_id="system",
                            account_id=session_id,
                            properties={
                                "session_id": session_id,
                                "result_count": len(all_results),
                                "participant_count": answers_data.get("participant_count", 0),
                                "attempt_number": attempt,
                                "answer_count": len(answers_data.get("answers", [])),
                            },
                        )
                        return
                    else:
                        logger.warning("Session %s: validation failed for %d results", session_id, len(results_response.results))

                except APITimeoutError:
                    logger.warning("Session %s: OpenAI timeout on attempt %d", session_id, attempt)
                    continue

                except (APIError, Exception):
                    logger.exception("Result generation failed for session %s on attempt %d", session_id, attempt)
                    return

            logger.error("Session %s: result generation exhausted all %d attempts", session_id, total_attempts)
            pendo_track(
                "result_generation_failed",
                visitor_id="system",
                account_id=session_id,
                properties={
                    "session_id": session_id,
                    "failure_reason": "exhausted_retries",
                    "attempts_made": total_attempts,
                    "had_answers": True,
                },
            )

        finally:
            if not succeeded:
                AIService._set_session_state(session_id, SessionState.ANSWERING)

    # region Result Generation Helpers

    @staticmethod
    def _generate_answer_summary(client: OpenAI, answers_data: dict) -> str | None:
        try:
            completion = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": ANSWER_SUMMARY_GENERATION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": AIService._build_summary_prompt(answers_data),
                    },
                ],
            )

            if completion.choices[0].message.content:
                return completion.choices[0].message.content
            return None

        except (APITimeoutError, APIError):
            return None

    @staticmethod
    def _generate_result_response(
        client: OpenAI, answer_summary: str, answers_data: dict, overall: AIResult | None = None
    ) -> AIResultsResponse | None:
        try:
            completion = client.beta.chat.completions.parse(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": RESULT_GENERATION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": AIService._build_result_prompt(answer_summary, answers_data, overall),
                    },
                ],
                response_format=AIResultsResponse,
            )

            result = completion.choices[0].message.parsed
            return result if result else None

        except (APITimeoutError, APIError):
            return None

    @staticmethod
    def _validate_results(results: list) -> bool:
        recommendations = [r for r in results if r.type == ResultType.RECOMMENDATION.value]
        if not (4 <= len(recommendations) <= 6):
            return False
        for result in recommendations:
            if not result.type or not result.value:
                return False
            if not re.search(r'\d', result.value):
                return False
        return True

    @staticmethod
    def _compute_question_stats(answers_by_question: dict) -> str:
        """Pre-compute aggregate statistics for SLIDER, NUMBER, MULTISELECT, and SWIPE questions."""
        lines: list[str] = []

        for (q_text, mechanic), values in answers_by_question.items():
            if mechanic == Mechanic.TEXT.value:
                continue

            stat_lines: list[str] = []

            if mechanic == Mechanic.NUMBER.value:
                nums = []
                for v in values:
                    try:
                        nums.append(int(v))
                    except (ValueError, TypeError):
                        pass
                if nums:
                    avg = sum(nums) / len(nums)
                    stat_lines.append(f"  n={len(nums)}, avg={avg:.1f}, min={min(nums)}, max={max(nums)}")

            elif mechanic == Mechanic.SLIDER.value:
                slider_vals = []
                for v in values:
                    try:
                        parsed = json.loads(v)
                        if isinstance(parsed, dict) and "value" in parsed:
                            slider_vals.append(float(parsed["value"]))
                    except (json.JSONDecodeError, TypeError, KeyError):
                        pass
                if slider_vals:
                    avg = sum(slider_vals) / len(slider_vals)
                    stat_lines.append(f"  n={len(slider_vals)}, avg={avg:.1f}, min={min(slider_vals)}, max={max(slider_vals)}")

            elif mechanic == Mechanic.MULTISELECT.value:
                option_counts: dict[str, int] = {}
                respondent_count = 0
                for v in values:
                    try:
                        options = json.loads(v)
                        if isinstance(options, list):
                            respondent_count += 1
                            for opt in options:
                                opt_str = str(opt)
                                option_counts[opt_str] = option_counts.get(opt_str, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        pass
                if option_counts:
                    stat_lines.append(f"  {respondent_count} respondents:")
                    for opt, count in sorted(option_counts.items(), key=lambda x: -x[1]):
                        stat_lines.append(f"    {opt}: {count}/{respondent_count}")

            elif mechanic == Mechanic.SWIPE.value:
                choice_counts: dict[str, int] = {}
                for v in values:
                    try:
                        choice = json.loads(v)
                        if isinstance(choice, str):
                            choice_counts[choice] = choice_counts.get(choice, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        pass
                if choice_counts:
                    total = sum(choice_counts.values())
                    for choice, count in sorted(choice_counts.items(), key=lambda x: -x[1]):
                        stat_lines.append(f"  {choice}: {count}/{total}")

            if stat_lines:
                lines.append(f"\nQ: {q_text} [{mechanic}]")
                lines.extend(stat_lines)

        if not lines:
            return ""

        return "PRE-CALCULATED STATISTICS (use these directly):\n" + "\n".join(lines)

    @staticmethod
    def _extract_overall_result(summary: str) -> AIResult | None:
        """Parse the CONSENSUS_RESULT tag from the answer summary and return an OVERALL AIResult."""
        match = re.search(r'CONSENSUS_RESULT:\s*\{', summary)
        if not match:
            logger.warning("CONSENSUS_RESULT tag not found in answer summary")
            return None
        try:
            data, _ = json.JSONDecoder().raw_decode(summary, match.end() - 1)
            return AIResult(
                type=ResultType.OVERALL.value,
                value=json.dumps({
                    "is_agreement": bool(data["is_agreement"]),
                    "key_insight": str(data["key_insight"]),
                }),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("Failed to parse CONSENSUS_RESULT JSON from answer summary")
            return None

    @staticmethod
    def _build_summary_prompt(answers_data: dict) -> str:
        answers = answers_data["answers"]
        participant_count = answers_data["participant_count"]

        # Stable anonymous tokens so the same participant is consistent across questions
        participant_ids = sorted(set(a["participant_id"] for a in answers))
        anon_map = {pid: f"Participant {i + 1}" for i, pid in enumerate(participant_ids)}

        # Group raw values by (question_text, mechanic) for stat computation
        answers_by_question: dict[tuple, list] = {}
        answers_by_q_text: dict[str, list] = {}
        for answer in answers:
            key = (answer["question_text"], answer["question_mechanic"])
            answers_by_question.setdefault(key, []).append(answer["value"])
            answers_by_q_text.setdefault(answer["question_text"], []).append(answer)

        prompt_parts = [f"Group size: {participant_count} participants\n"]

        stats_block = AIService._compute_question_stats(answers_by_question)
        if stats_block:
            prompt_parts.append(stats_block)
            prompt_parts.append("")

        prompt_parts.append("QUESTION-BY-QUESTION ANSWERS:\n")
        for q_text, q_answers in answers_by_q_text.items():
            mechanic = q_answers[0]["question_mechanic"] if q_answers else ""
            prompt_parts.append(f"\nQ: {q_text}")
            if mechanic == Mechanic.TEXT.value:
                # No attribution for open-text — numbered list only
                for i, answer in enumerate(q_answers, start=1):
                    prompt_parts.append(f"  [{i}] {answer['value']}")
            else:
                for answer in q_answers:
                    anon = anon_map.get(answer["participant_id"], "Participant ?")
                    prompt_parts.append(f"  - {anon}: {answer['value']}")

        prompt_parts.append(
            "\n\nProvide a structured summary that highlights the group's collective preferences, "
            "agreement areas, and divergence points. Be specific and quantitative where possible."
        )

        return "\n".join(prompt_parts)

    @staticmethod
    def _build_result_prompt(answer_summary: str, answers_data: dict, overall: AIResult | None = None) -> str:
        answers = answers_data["answers"]

        participant_ids = sorted(set(a["participant_id"] for a in answers))
        anon_map = {pid: f"Participant {i + 1}" for i, pid in enumerate(participant_ids)}

        prompt_parts = [
            "GROUP ANSWER SUMMARY:\n",
            answer_summary,
            "\n\nDETAILED ANSWER DATA:\n",
        ]

        for answer in answers:
            mechanic = answer["question_mechanic"]
            if mechanic == Mechanic.TEXT.value:
                prompt_parts.append(f"- [Anonymous] [TEXT]: {answer['value']}")
            else:
                anon = anon_map.get(answer["participant_id"], "Participant ?")
                prompt_parts.append(f"- {anon} [{mechanic}]: {answer['value']}")

        if overall:
            try:
                overall_data = json.loads(overall.value)
                consensus_label = "YES" if overall_data.get("is_agreement") else "NO"
                prompt_parts.append(
                    f"\n\nOVERALL CONSENSUS: {consensus_label} — {overall_data.get('key_insight', '')}"
                )
            except (json.JSONDecodeError, TypeError):
                pass

        prompt_parts.append(
            "\n\nBased on this group's preferences and constraints, generate 4–6 RECOMMENDATION results. "
            "Each recommendation should explicitly reference the group data that supports it."
        )

        return "\n".join(prompt_parts)

    # endregion

    # region Helpers

    @staticmethod
    def _set_session_state(session_id: str, state: SessionState) -> None:
        db = SessionLocal()
        try:
            session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
            if session:
                session.state = state
                db.commit()
                logger.info("Session %s state reset to %s", session_id, state.value)
        except Exception:
            db.rollback()
            logger.warning("Failed to reset session %s state to %s", session_id, state.value)
        finally:
            db.close()

    @staticmethod
    def _build_user_prompt(
        topic: str, context: str | None,
    ) -> str:
        parts = [f"Topic: {topic}"]
        if context:
            parts.append(f"Context: {context}")
        return "\n".join(parts)

    @staticmethod
    def _validate_response(questions: list[AIQuestion]) -> bool:
        if not (AI_MIN_QUESTIONS <= len(questions) <= AI_MAX_QUESTIONS):
            return False

        for q in questions:
            if q.mechanic == Mechanic.MULTISELECT:
                if not q.options:
                    return False
                last = q.options[-1].strip().lower().replace(" ", "")
                if last != "other/any":
                    return False
                
            if q.mechanic == Mechanic.SWIPE:
                if not q.options or len(q.options) != 2:
                    return False
                

        return True

    # endregion
