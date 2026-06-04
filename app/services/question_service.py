import uuid as _uuid

from sqlalchemy.orm import Session as DBSession

from app.models.question import Question, QuestionOption
from app.schemas.ai import AIQuestion


class QuestionService:
    @staticmethod
    def save_questions(db: DBSession, session_id: str, questions: list[AIQuestion]) -> None:
        """Persist generated questions to database."""
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

                if len(q.options) > 0:
                    for order, label in enumerate(q.options, start=1):
                        db.add(QuestionOption(question_id=question.id, label=label, display_order=order))

            db.commit()
        except Exception:
            db.rollback()
            raise
