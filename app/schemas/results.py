from pydantic import BaseModel


class CategoryResult(BaseModel):
    category_id: str
    name: str
    yes_count: int
    no_count: int
    overlap_score: float


class ResultsResponse(BaseModel):
    results: list[CategoryResult]
    has_consensus: bool
    top_pick: str | None = None
