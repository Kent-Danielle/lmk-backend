import uuid
from datetime import datetime
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Answer(Base):
    __tablename__ = "answers"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False)
    question_id    = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    value          = Column(Text, nullable=False)  # stored as JSON string; parse in service layer
    answered_at    = Column(TIMESTAMP, default=datetime.utcnow)

    participant = relationship("Participant", back_populates="answers")
    question    = relationship("Question", back_populates="answers")
