from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.base import APIResponse
from app.schemas.question import SubmitAnswersRequest
from app.services.answer_service import AnswerService

router = APIRouter(prefix="/sessions/{session_id}", tags=["answers"])


@router.post("/answers", response_model=APIResponse)
async def submit_answers(
    session_id: str,
    body: SubmitAnswersRequest,
    db: Session = Depends(get_db),
):
    data = AnswerService.submit_answers(db, session_id, body)
    return APIResponse(success=True, data=data)