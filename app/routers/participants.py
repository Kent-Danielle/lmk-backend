from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.base import APIResponse
from app.schemas.participant import JoinSessionRequest
from app.services.participant_service import ParticipantService

router = APIRouter(prefix="/sessions/{session_id}/participants", tags=["participants"])


@router.post("/", response_model=APIResponse)
async def join_session(
    session_id: str,
    body: JoinSessionRequest,
    db: Session = Depends(get_db),
):
    data = ParticipantService.join(db, session_id, body)
    return APIResponse(success=True, data=data.model_dump())
