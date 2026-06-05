import json
import asyncio

from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.db import get_db
from app.middleware.rate_limit import limiter
from app.schemas.base import APIResponse
from app.schemas.session import (
    CreateSessionRequest,
    AdvanceRequest,
)
from app.services.event_manager import event_manager
from app.services.session_service import SessionService
from app.services.ai_service import AIService
from app.services.result_service import ResultService
from app.services.participant_service import ParticipantService
from app.services.pendo_service import pendo_track

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=APIResponse)
@limiter.limit("5/minute")
def create_session(
    request: Request,
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
):
    data = SessionService.create(db, body)
    return APIResponse(success=True, data=data.model_dump())

# IMPORTANT: declare this BEFORE /{session_id} and after link/{session_id} to avoid route conflicts 
@router.get("/{session_id}/stream")
async def stream_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    data = SessionService.get_by_session_id(db, session_id)

    pendo_track(
        "session_state_subscribed",
        visitor_id="system",
        account_id=session_id,
        properties={
            "session_id": session_id,
            "current_state": data.state.value,
        },
    )

    queue = event_manager.subscribe(session_id)

    async def generator():
        try:
            yield {
                "event": "state_change",
                "data": json.dumps({"state": data.state.value}),
            }

            while True:
                state = await queue.get()
                yield {
                    "event": "state_change",
                    "data": json.dumps({"state": state}),
                }
        except asyncio.CancelledError:
            event_manager.unsubscribe(session_id, queue)
            raise

    return EventSourceResponse(generator())

@router.get("/{session_id}", response_model=APIResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    data = SessionService.get_by_session_id(db, session_id)
    return APIResponse(success=True, data=data.model_dump())


@router.get(
    "/{session_id}/state",
    response_model=APIResponse,
    deprecated=True,
    description="Deprecated: will be replaced by an SSE-based endpoint for real-time state updates.",
)
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    data = SessionService.get_state(db, session_id)
    return APIResponse(success=True, data=data.model_dump())


@router.post("/{session_id}/advance", response_model=APIResponse)
@limiter.limit("10/minute")
async def advance_session(
    request: Request,
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


@router.get("/{session_id}/participants/{participant_id}/answered", response_model=APIResponse)
async def has_participant_answered(
    session_id: str,
    participant_id: str,
    db: Session = Depends(get_db),
):
    answered = ParticipantService.has_answered(db, session_id, participant_id)
    return APIResponse(success=True, data={"answered": answered})

@router.get("/{session_id}/participants/answered", response_model=APIResponse)
async def get_answered_participants(
    session_id: str,
    db: Session = Depends(get_db),
):
    data = ParticipantService.get_all_participants_answered(db, session_id)
    return APIResponse(success=True, data=data)

@router.get("/{session_id}/results_ready", response_model=APIResponse)
async def get_participants_answered(
    session_id: str,
    db: Session = Depends(get_db),
):
    ready = ResultService.are_results_ready(db, session_id)
    return APIResponse(success=True, data={"results_ready": ready}
)

@router.get("/{session_id}/results", response_model=APIResponse)
async def get_results(
    session_id: str,
    db: Session = Depends(get_db),
):
    data = ResultService.get_results(db, session_id)

    pendo_track(
        "results_viewed",
        visitor_id="system",
        account_id=session_id,
        properties={
            "session_id": session_id,
            "result_count": len(data.results),
        },
    )

    return APIResponse(success=True, data=data.model_dump())
