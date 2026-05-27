import uuid as _uuid

from sqlalchemy.orm import Session as DBSession

from app.constants import ResultType
from app.models.result import Result
from app.schemas.ai import AIResult


class ResultService:
    @staticmethod
    def save_results(db: DBSession, session_id: str, results: list[AIResult]) -> None:
        """Persist generated results to database."""
        try:
            session_uuid = _uuid.UUID(session_id)
            for result in results:
                db.add(
                    Result(
                        session_id=session_uuid,
                        type = result.type,
                        value = result.value,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
