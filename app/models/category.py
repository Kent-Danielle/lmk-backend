import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base


class CategoryOption(Base):
    __tablename__ = "category_options"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    name       = Column(Text, nullable=False)
    reasoning  = Column(Text, nullable=False)

    session = relationship("Session", back_populates="category_options")
