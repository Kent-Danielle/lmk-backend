from fastapi import APIRouter, HTTPException

from app.schemas.base import APIResponse
from app.schemas.participant import JoinSessionRequest, JoinSessionResponse

router = APIRouter(prefix="/sessions/{session_id}/participants", tags=["participants"])


@router.post("/", response_model=APIResponse)
async def join_session(session_id: str, body: JoinSessionRequest):
    # TODO: call ParticipantService.join
    raise HTTPException(status_code=501, detail="Not implemented")
