from pydantic import BaseModel
from typing import Any

from app.constants import Mechanic


class ConsensusPoint(BaseModel):
    question_id: str
    mechanic: Mechanic
    summary: str


class DivergencePoint(BaseModel):
    question_id: str
    mechanic: Mechanic
    summary: str


class QuestionAggregate(BaseModel):
    question_id: str
    text: str
    mechanic: Mechanic
    aggregated: Any


class RevealResponse(BaseModel):
    consensus: list[ConsensusPoint]
    divergence: list[DivergencePoint]
    aggregates: list[QuestionAggregate]
