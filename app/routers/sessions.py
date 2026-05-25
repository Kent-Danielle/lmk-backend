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
from app.schemas.reveal import RevealResponse
from app.schemas.category import CategoriesResponse
from app.schemas.results import ResultsResponse
from app.services.session_service import SessionService

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
async def advance_session(session_id: str, body: AdvanceRequest):
    # TODO: call SessionService.advance (host only)
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}/reveal", response_model=APIResponse)
async def get_reveal(session_id: str):
    # TODO: call ResultsService.get_reveal
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}/categories", response_model=APIResponse)
async def get_categories(session_id: str):
    # TODO: call AIService.get_categories
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{session_id}/results", response_model=APIResponse)
async def get_results(session_id: str):
    # TODO: call ResultsService.get_results
    raise HTTPException(status_code=501, detail="Not implemented")
