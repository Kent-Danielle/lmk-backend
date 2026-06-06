from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

from app.constants import SessionState, MAX_TOPIC_LEN, MAX_CONTEXT_LEN, MAX_NAME_LEN
from app.utils.sanitize import sanitize


class CreateSessionRequest(BaseModel):
    topic: str
    context: Optional[str] = None
    host_display_name: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        return sanitize(v, MAX_TOPIC_LEN)

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: Optional[str]) -> Optional[str]:
        return sanitize(v, MAX_CONTEXT_LEN) if v is not None else v

    @field_validator("host_display_name")
    @classmethod
    def validate_host_display_name(cls, v: str) -> str:
        return sanitize(v, MAX_NAME_LEN)


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
