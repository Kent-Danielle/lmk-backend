from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.constants import SessionState, MAX_HOST_NOTES_LENGTH


class CreateSessionRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    host_notes: Optional[str] = Field(default=None, max_length=MAX_HOST_NOTES_LENGTH)
    host_display_name: str


class SessionOut(BaseModel):
    id: str
    topic: str
    context: Optional[str] = None
    state: SessionState
    join_link: str
    created_at: datetime


class CreateSessionResponse(BaseModel):
    session_id: str
    host_participant_id: str
    join_link: str


class SessionStateResponse(BaseModel):
    state: SessionState
    results_ready: bool = False


class AdvanceRequest(BaseModel):
    participant_id: str
