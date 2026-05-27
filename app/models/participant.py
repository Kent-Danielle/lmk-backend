import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class Participant(Base):
    __tablename__ = "participants"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id    = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    display_name  = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=True)
    joined_at     = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="participants",
                           foreign_keys=[session_id])
    answers = relationship("Answer", back_populates="participant")
