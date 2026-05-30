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
from app.schemas.ai import AIQuestion, AIQuestionsResponse, AIResultsResponse
from app.schemas.question import QuestionOut, QuestionOptionOut
from app.constants import AI_MAX_QUESTIONS, AI_MIN_QUESTIONS, Mechanic, AI_TIMEOUT_SECONDS, AI_MAX_RETRIES, SessionState
from app.services.event_manager import event_manager
from app.utils.prompts import ANSWER_SUMMARY_GENERATION_SYSTEM_PROMPT, RESULT_GENERATION_SYSTEM_PROMPT, QUESTION_GENERATION_SYSTEM_PROMPT
from app.utils.http import HTTPStatusCode, HTTPErrorMessage
from app.services.question_service import QuestionService
from app.services.result_service import ResultService
from app.services.answer_service import AnswerService

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
        host_notes: str | None,
    ) -> None:
        logger.info("Starting question generation for session %s", session_id)
        user_prompt = AIService._build_user_prompt(topic, context, host_notes)
        total_attempts = AI_MAX_RETRIES + 1

        for attempt in range(1, total_attempts + 1):
            try:
                logger.info("Session %s: question generation attempt %d/%d", session_id, attempt, total_attempts)
                result_response = AIService._generate_questions_response(_openai_client, user_prompt)
                if result_response is None:
                    logger.warning("Session %s: received null response from OpenAI", session_id)
                    return

                if not result_response.valid:
                    logger.warning("Session %s: response marked as invalid by AI", session_id)
                    return

                if AIService._validate_response(result_response.questions):
                    logger.info("Session %s: validation passed with %d questions, saving", session_id, len(result_response.questions))
                    db = SessionLocal()
                    try:
                        QuestionService.save_questions(db, session_id, result_response.questions)
                    finally:
                        db.close()
                    return
                else:
                    logger.warning("Session %s: validation failed for %d questions", session_id, len(result_response.questions))

            except APITimeoutError:
                logger.warning("Session %s: OpenAI timeout on attempt %d", session_id, attempt)
                continue

            except (APIError, Exception):
                logger.exception("Question generation failed for session %s on attempt %d", session_id, attempt)
                return
        logger.error("Session %s: question generation exhausted all %d attempts", session_id, total_attempts)

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
                    QuestionOptionOut(id=str(o.id), label=o.label)
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

                logger.info("Session %s: generating result response", session_id)
                results_response = AIService._generate_result_response(
                    _openai_client, answer_summary, answers_data
                )

                if results_response is None or not results_response.valid:
                    logger.warning("Session %s: result response null or invalid, retrying", session_id)
                    continue

                if AIService._validate_results(results_response.results):
                    logger.info("Session %s: validation passed with %d results, saving", session_id, len(results_response.results))
                    db = SessionLocal()
                    try:
                        ResultService.save_results(db, session_id, results_response.results)
                        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
                        if session:
                            session.state = SessionState.RESULTS
                            db.commit()

                            event_manager.publish(session_id, SessionState.RESULTS.value)
                    finally:
                        db.close()
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
        client: OpenAI, answer_summary: str, answers_data: dict
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
                        "content": AIService._build_result_prompt(answer_summary, answers_data),
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
        if not (4 <= len(results) <= 6):
            return False
        for result in results:
            if not result.type or not result.value:
                return False
            if not re.search(r'\d', result.value):
                return False
        return True

    @staticmethod
    def _build_summary_prompt(answers_data: dict) -> str:
        answers = answers_data["answers"]
        participant_count = answers_data["participant_count"]

        # Group answers by question for better summarization
        answers_by_question = {}
        for answer in answers:
            q_text = answer["question_text"]
            if q_text not in answers_by_question:
                answers_by_question[q_text] = []
            answers_by_question[q_text].append(answer)

        prompt_parts = [
            f"Group size: {participant_count} participants\n",
            "QUESTION-BY-QUESTION ANSWERS:\n",
        ]

        for q_text, q_answers in answers_by_question.items():
            prompt_parts.append(f"\nQ: {q_text}")
            for answer in q_answers:
                prompt_parts.append(
                    f"  - {answer['participant_name']}: {answer['value']}"
                )

        prompt_parts.append(
            "\n\nProvide a structured summary that highlights the group's collective preferences, "
            "agreement areas, and divergence points. Be specific and quantitative where possible."
        )

        return "\n".join(prompt_parts)

    @staticmethod
    def _build_result_prompt(answer_summary: str, answers_data: dict) -> str:
        prompt_parts = [
            "GROUP ANSWER SUMMARY:\n",
            answer_summary,
            "\n\nDETAILED ANSWER DATA:\n",
        ]

        # Include structured answer data for precise reasoning
        for answer in answers_data["answers"]:
            prompt_parts.append(
                f"- {answer['participant_name']} [{answer['question_mechanic']}]: {answer['value']}"
            )

        prompt_parts.append(
            f"\n\nBased on this group's preferences and constraints, generate {AI_MIN_QUESTIONS}–{AI_MAX_QUESTIONS} result recommendations. "
            "Each recommendation should explicitly reference the group data that supports it."
        )

        return "\n".join(prompt_parts)

    # endregion

    # region Helpers

    @staticmethod
    def _build_user_prompt(
        topic: str, context: str | None, host_notes: str | None,
    ) -> str:
        parts = [f"Topic: {topic}"]
        if context:
            parts.append(f"Context: {context}")
        if host_notes:
            parts.append(f"Host notes: {host_notes}")
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
