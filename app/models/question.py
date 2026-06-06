import uuid
from sqlalchemy import Column, Integer, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.constants import Mechanic


class Question(Base):
    __tablename__ = "questions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id    = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    text          = Column(Text, nullable=False)
    mechanic      = Column(Enum(Mechanic), nullable=False)
    display_order = Column(Integer, nullable=False)

    session = relationship("Session", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.display_order")
    answers = relationship("Answer", back_populates="question")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id   = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label         = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)

    question = relationship("Question", back_populates="options")
