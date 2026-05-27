import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.constants import SessionState


class Session(Base):
    __tablename__ = "sessions"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic          = Column(Text, nullable=False)
    context        = Column(Text, nullable=True)
    state          = Column(Enum(SessionState), nullable=False, default=SessionState.ANSWERING)
    host_id        = Column(UUID(as_uuid=True), ForeignKey("participants.id", use_alter=True), nullable=True)
    expected_count = Column(Integer, nullable=False)
    deadline       = Column(TIMESTAMP, nullable=True)
    answered_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at     = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    participants     = relationship("Participant", back_populates="session",
                                    foreign_keys="Participant.session_id")
    questions        = relationship("Question", back_populates="session")
    category_options = relationship("CategoryOption", back_populates="session")
