from pydantic import BaseModel
from typing import Any

from app.constants import ResultType


class ResultOut(BaseModel):
    id: str
    type: ResultType
    value: Any


class ResultsResponse(BaseModel):
    results: list[ResultOut]
