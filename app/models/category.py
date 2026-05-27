import uuid
from sqlalchemy import Column, Text, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.constants import SwipeDirection


class CategoryOption(Base):
    __tablename__ = "category_options"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    name       = Column(Text, nullable=False)
    reasoning  = Column(Text, nullable=False)

    session = relationship("Session", back_populates="category_options")
    swipes  = relationship("Swipe", back_populates="category")
