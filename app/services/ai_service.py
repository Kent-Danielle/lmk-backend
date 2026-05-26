import os
import uuid as _uuid

from openai import OpenAI, APITimeoutError, APIError
from sqlalchemy.orm import Session as DBSession, joinedload
from fastapi import HTTPException

from app.db import SessionLocal
from app.models.session import Session
from app.models.question import Question, QuestionOption
from app.schemas.ai import AIQuestion, AIQuestionsResponse
from app.schemas.question import QuestionOut, QuestionOptionOut
from app.constants import Mechanic, AI_MODEL, AI_TIMEOUT_SECONDS, AI_MAX_RETRIES
from app.utils.prompts import QUESTION_GENERATION_SYSTEM_PROMPT
from app.utils.http import HTTPStatusCode, HTTPErrorMessage


class AIService:
    @staticmethod
    def generate_questions(
        session_id: str,
        topic: str,
        context: str | None,
        host_notes: str | None,
    ) -> None:
        """Generate AI questions for a session and persist them.

        Runs as a BackgroundTask — owns its own DB session and OpenAI client.
        Retries up to AI_MAX_RETRIES times on validation failures or timeouts.
        """
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=AI_TIMEOUT_SECONDS,
        )
        user_prompt = AIService._build_user_prompt(topic, context, host_notes)
        total_attempts = AI_MAX_RETRIES + 1

        for attempt in range(1, total_attempts + 1):
            try:
                completion = client.beta.chat.completions.parse(
                    model=AI_MODEL,
                    messages=[
                        {"role": "system", "content": QUESTION_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=AIQuestionsResponse,
                )

                result = completion.choices[0].message.parsed
                if result is None:
                    return

                if not result.valid:
                    return

                if AIService._validate_response(result.questions):
                    AIService._save_questions(session_id, result.questions)
                    return

            except APITimeoutError:
                continue

            except (APIError, Exception):
                return

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
    def generate_categories(session_id: str) -> None:
        # TODO: A5 — OpenAI Call 2, validate reasoning cites numbers, save to DB
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        if not (4 <= len(questions) <= 6):
            return False

        for i in range(1, len(questions)):
            if questions[i].mechanic == questions[i - 1].mechanic:
                return False

        for q in questions:
            if q.mechanic == Mechanic.MULTISELECT:
                if not q.options:
                    return False
                last = q.options[-1].strip().lower().replace(" ", "")
                if last != "other/any":
                    return False

        return True

    @staticmethod
    def _save_questions(session_id: str, questions: list[AIQuestion]) -> None:
        db = SessionLocal()
        try:
            for order, q in enumerate(questions, start=1):
                question = Question(
                    session_id=_uuid.UUID(session_id),
                    text=q.text,
                    mechanic=q.mechanic,
                    display_order=order,
                )
                db.add(question)
                db.flush()

                if q.mechanic == Mechanic.MULTISELECT:
                    for label in q.options:
                        db.add(QuestionOption(question_id=question.id, label=label))

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
