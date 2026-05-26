from fastapi import APIRouter, HTTPException

from app.schemas.base import APIResponse
from app.schemas.category import SwipeSubmission
from app.utils.http import HTTPStatusCode, HTTPErrorMessage

router = APIRouter(prefix="/sessions/{session_id}/swipes", tags=["swipes"])


@router.post("/", response_model=APIResponse)
async def submit_swipe(session_id: str, body: SwipeSubmission):
    # TODO: call SwipeService.submit
    raise HTTPException(
        status_code=HTTPStatusCode.NOT_IMPLEMENTED,
        detail=HTTPErrorMessage.NOT_IMPLEMENTED,
    )
