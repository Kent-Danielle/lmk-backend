from fastapi import APIRouter, HTTPException

from app.schemas.base import APIResponse
from app.schemas.category import SwipeSubmission

router = APIRouter(prefix="/sessions/{session_id}/swipes", tags=["swipes"])


@router.post("/", response_model=APIResponse)
async def submit_swipe(session_id: str, body: SwipeSubmission):
    # TODO: call SwipeService.submit
    raise HTTPException(status_code=501, detail="Not implemented")
