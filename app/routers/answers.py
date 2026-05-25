from fastapi import APIRouter, HTTPException

from app.schemas.base import APIResponse
from app.schemas.question import QuestionOut, SubmitAnswersRequest

router = APIRouter(prefix="/sessions/{session_id}", tags=["answers"])


@router.get("/questions", response_model=APIResponse)
async def get_questions(session_id: str):
    # TODO: call SessionService.get_questions
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/answers", response_model=APIResponse)
async def submit_answers(session_id: str, body: SubmitAnswersRequest):
    # TODO: call AnswerService.submit
    raise HTTPException(status_code=501, detail="Not implemented")
