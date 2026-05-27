from pydantic import BaseModel


class CategoryOptionOut(BaseModel):
    id: str
    name: str
    reasoning: str


class CategoriesResponse(BaseModel):
    categories: list[CategoryOptionOut]
