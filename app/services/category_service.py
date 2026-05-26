import uuid as _uuid

from sqlalchemy.orm import Session as DBSession

from app.models.swipe import CategoryOption
from app.schemas.ai import AICategory


class CategoryService:
    @staticmethod
    def save_categories(db: DBSession, session_id: str, categories: list[AICategory]) -> None:
        """Persist generated categories to database."""
        try:
            session_uuid = _uuid.UUID(session_id)
            for category in categories:
                db.add(
                    CategoryOption(
                        session_id=session_uuid,
                        name=category.name,
                        reasoning=category.reasoning,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
