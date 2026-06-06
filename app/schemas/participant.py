from pydantic import BaseModel, field_validator
from typing import Optional

from app.constants import MAX_NAME_LEN
from app.utils.sanitize import sanitize


class JoinSessionRequest(BaseModel):
    display_name: str

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        return sanitize(v, MAX_NAME_LEN)


class JoinSessionResponse(BaseModel):
    participant_id: str
    session_id: str
