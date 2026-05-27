from pydantic import BaseModel
from typing import Optional


class JoinSessionRequest(BaseModel):
    display_name: str
    password: Optional[str] = None


class JoinSessionResponse(BaseModel):
    participant_id: str
