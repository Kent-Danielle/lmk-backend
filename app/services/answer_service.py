import uuid as _uuid

from sqlalchemy.orm import Session as DBSession

from app.models.answer import Answer
from app.models.question import Question
from app.db import SessionLocal


class AnswerService:
    @staticmethod
    def fetch_session_answers(session_id: str) -> dict | None:
        """Fetch all answers for a session with question and participant context."""
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

            # Structure answers with question and participant info for AI context
            structured_answers = []
            for answer in answers:
                structured_answers.append({
                    "participant_id": str(answer.participant.id),
                    "participant_name": answer.participant.display_name,
                    "question_text": answer.question.text,
                    "question_mechanic": answer.question.mechanic.value,
                    "value": answer.value,  # JSON string; AI will parse as needed
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
