import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("participant_id", "question_id", name="uq_answer_participant_question"),
    )

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    question_id    = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    value          = Column(Text, nullable=False)  # stored as JSON string; parse in service layer
    answered_at    = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    participant = relationship("Participant", back_populates="answers")
    question    = relationship("Question", back_populates="answers")
