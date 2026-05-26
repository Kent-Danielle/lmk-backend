from fastapi import APIRouter, HTTPException

from app.schemas.base import APIResponse
from app.schemas.participant import JoinSessionRequest, JoinSessionResponse
from app.utils.http import HTTPStatusCode, HTTPErrorMessage

router = APIRouter(prefix="/sessions/{session_id}/participants", tags=["participants"])


@router.post("/", response_model=APIResponse)
async def join_session(session_id: str, body: JoinSessionRequest):
    # TODO: call ParticipantService.join
    raise HTTPException(
        status_code=HTTPStatusCode.NOT_IMPLEMENTED,
        detail=HTTPErrorMessage.NOT_IMPLEMENTED,
    )
