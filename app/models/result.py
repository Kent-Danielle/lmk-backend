import uuid
from sqlalchemy import Column, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.constants import ResultType
from app.db import Base


class Result(Base):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(ResultType), nullable=False)
    value = Column(Text, nullable=False)  # stored as JSON string; parse in service layer

    session = relationship("Session", back_populates="results")
