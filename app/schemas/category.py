from pydantic import BaseModel

from app.constants import SwipeDirection


class CategoryOptionOut(BaseModel):
    id: str
    name: str
    reasoning: str


class CategoriesResponse(BaseModel):
    categories: list[CategoryOptionOut]


class SwipeSubmission(BaseModel):
    participant_id: str
    category_id: str
    direction: SwipeDirection
