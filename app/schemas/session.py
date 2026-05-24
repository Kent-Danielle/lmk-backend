from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.constants import SessionState


class CreateSessionRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    expected_count: int
    host_notes: Optional[str] = None


class SessionOut(BaseModel):
    id: str
    topic: str
    context: Optional[str] = None
    state: SessionState
    expected_count: int
    answered_count: int
    created_at: datetime


class CreateSessionResponse(BaseModel):
    session_id: str
    join_link: str


class SessionStateResponse(BaseModel):
    state: SessionState
    participants_answered: int
    expected: int


class AdvanceRequest(BaseModel):
    participant_id: str
