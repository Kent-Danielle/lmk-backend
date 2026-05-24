from pydantic import BaseModel
from typing import Optional, Any

from app.constants import Mechanic


class QuestionOptionOut(BaseModel):
    id: str
    label: str


class QuestionOut(BaseModel):
    id: str
    text: str
    mechanic: Mechanic
    display_order: int
    options: list[QuestionOptionOut] = []


class AnswerSubmission(BaseModel):
    question_id: str
    value: Any


class SubmitAnswersRequest(BaseModel):
    participant_id: str
    answers: list[AnswerSubmission]
