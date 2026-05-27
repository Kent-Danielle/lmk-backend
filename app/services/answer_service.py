from datetime import datetime, timezone
import json
import uuid as _uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from app.constants import Mechanic
from app.models.answer import Answer
from app.models.question import Question
from app.db import SessionLocal
from app.models.session import Session
from app.schemas.question import SubmitAnswersRequest
from app.utils.http import HTTPErrorMessage, HTTPStatusCode


def _validate_answer(mechanic, value) -> str:
    if mechanic == Mechanic.TEXT:
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(status_code=400, detail="TEXT must be a non-empty string.")
        return value
    if mechanic == Mechanic.MULTISELECT:
        if not isinstance(value, list):
            raise HTTPException(status_code=400, detail="MULTISELECT must be an array.")
        return json.dumps(value)
    if mechanic == Mechanic.SLIDER:
        if not isinstance(value, dict) or "value" not in value:
            raise HTTPException(status_code=400, detail="SLIDER must be an object with a 'value' key.")
        return json.dumps(value)


class AnswerService:
    @staticmethod
    def fetch_session_answers(session_id: str) -> dict | None:
        db = SessionLocal()
        try:
            answers = (
                db.query(Answer)
                .join(Answer.question)
                .join(Answer.participant)
                .filter(Question.session_id == _uuid.UUID(session_id))
                .all()
            )

            if not answers:
                return None

            structured_answers = []
            for answer in answers:
                structured_answers.append({
                    "participant_id": str(answer.participant.id),
                    "participant_name": answer.participant.display_name,
                    "question_text": answer.question.text,
                    "question_mechanic": answer.question.mechanic.value,
                    "value": answer.value,
                })

            return {
                "session_id": session_id,
                "answers": structured_answers,
                "participant_count": len(set(a["participant_id"] for a in structured_answers)),
            }
        except Exception:
            return None
        finally:
            db.close()

    @staticmethod
    def submit_answers(
        db: DBSession,
        session_id: str,
        body: SubmitAnswersRequest,
    ) -> dict:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )

        questions = {
            str(q.id): q
            for q in db.query(Question).filter(Question.session_id == session.id).all()
        }

        submitted = 0

        for submission in body.answers:
            question = questions.get(submission.question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question not found.")

            serialized = _validate_answer(question.mechanic, submission.value)

            try:
                db.add(Answer(
                    participant_id=_uuid.UUID(body.participant_id),
                    question_id=question.id,
                    value=serialized,
                    answered_at=datetime.now(timezone.utc)
                ))
                db.flush()
                submitted += 1
            except IntegrityError as e:
                db.rollback()
                if isinstance(e.orig, UniqueViolation):
                    continue
                raise

        db.commit()
        return {
            "submitted": submitted
        }