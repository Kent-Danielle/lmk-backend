from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.base import APIResponse
from app.schemas.session import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionOut,
    SessionStateResponse,
    AdvanceRequest,
)
from app.services.session_service import SessionService
from app.services.ai_service import AIService
from app.services.result_service import ResultService
from app.utils.http import HTTPStatusCode, HTTPErrorMessage

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=APIResponse)
async def create_session(
    body: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = SessionService.create(db, body, background_tasks)
    return APIResponse(success=True, data=data.model_dump())


@router.get("/{session_id}", response_model=APIResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    data = SessionService.get(db, session_id)
    return APIResponse(success=True, data=data.model_dump())


@router.get("/{session_id}/state", response_model=APIResponse)
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    data = SessionService.get_state(db, session_id)
    return APIResponse(success=True, data=data.model_dump())


@router.post("/{session_id}/advance", response_model=APIResponse)
async def advance_session(
    session_id: str,
    body: AdvanceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = SessionService.advance_state(db, session_id, body.participant_id, background_tasks)
    return APIResponse(success=True, data=data.model_dump())


@router.get("/{session_id}/questions", response_model=APIResponse)
async def get_questions(
    session_id: str,
    db: Session = Depends(get_db),
):
    data = AIService.get_questions(db, session_id)
    return APIResponse(success=True, data=[q.model_dump() for q in data])


@router.get("/{session_id}/results", response_model=APIResponse)
async def get_results(
    session_id: str,
    db: Session = Depends(get_db),
):
    data = ResultService.get_results(db, session_id)
    return APIResponse(success=True, data=data.model_dump())
