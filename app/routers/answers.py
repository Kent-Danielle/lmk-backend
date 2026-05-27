from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.base import APIResponse
from app.schemas.question import QuestionOut, SubmitAnswersRequest
from app.services.answer_service import AnswerService
from app.utils.http import HTTPStatusCode, HTTPErrorMessage

router = APIRouter(prefix="/sessions/{session_id}", tags=["answers"])


@router.get("/questions", response_model=APIResponse)
async def get_questions(session_id: str):
    # TODO: call SessionService.get_questions
    raise HTTPException(
        status_code=HTTPStatusCode.NOT_IMPLEMENTED,
        detail=HTTPErrorMessage.NOT_IMPLEMENTED,
    )


@router.post("/answers", response_model=APIResponse)
async def submit_answers(
    session_id: str,
    body: SubmitAnswersRequest,
    db: Session = Depends(get_db),
):
    data = AnswerService.submit_answers(db, session_id, body)
    return APIResponse(success=True, data=data)