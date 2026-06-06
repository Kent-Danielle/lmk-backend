from pydantic import BaseModel, field_validator
from typing import Optional, Any

from app.constants import Mechanic, MAX_ANSWER_TEXT_LEN
from app.utils.sanitize import sanitize


class QuestionOptionOut(BaseModel):
    id: str
    label: str
    display_order: int


class QuestionOut(BaseModel):
    id: str
    text: str
    mechanic: Mechanic
    display_order: int
    options: list[QuestionOptionOut] = []


class AnswerSubmission(BaseModel):
    question_id: str
    value: Any

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        if isinstance(v, str):
            return sanitize(v, MAX_ANSWER_TEXT_LEN)
        return v


class SubmitAnswersRequest(BaseModel):
    participant_id: str
    answers: list[AnswerSubmission]
