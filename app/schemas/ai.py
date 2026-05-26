from pydantic import BaseModel

from app.constants import Mechanic


class AIQuestion(BaseModel):
    text: str
    mechanic: Mechanic
    options: list[str]
    display_order: int


class AIQuestionsResponse(BaseModel):
    valid: bool
    questions: list[AIQuestion]


class AICategory(BaseModel):
    name: str
    reasoning: str


class AICategoriesResponse(BaseModel):
    valid: bool
    categories: list[AICategory]
