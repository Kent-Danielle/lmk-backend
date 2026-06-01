from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.constants import SessionState


class CreateSessionRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    host_display_name: str


class SessionInfoResponse(BaseModel):
    id: str
    topic: str
    context: Optional[str] = None
    state: SessionState
    join_link: str
    created_at: datetime
    host_id: str


class CreateSessionResponse(BaseModel):
    session_id: str
    host_participant_id: str
    join_link: str


class SessionStateResponse(BaseModel):
    state: SessionState
    results_ready: bool = False


class AdvanceRequest(BaseModel):
    participant_id: str
