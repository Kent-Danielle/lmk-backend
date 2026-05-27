from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.constants import SessionState, MAX_HOST_NOTES_LENGTH


class CreateSessionRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    expected_count: int
    host_notes: Optional[str] = Field(default=None, max_length=MAX_HOST_NOTES_LENGTH)
    host_display_name: str


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
    host_participant_id: str
    join_link: str


class SessionStateResponse(BaseModel):
    state: SessionState
    participants_answered: int
    expected: int
    results_ready: bool = False


class AdvanceRequest(BaseModel):
    participant_id: str
