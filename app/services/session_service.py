import uuid as _uuid

from sqlalchemy.orm import Session as DBSession
from fastapi import BackgroundTasks, HTTPException

from app.db import SessionLocal
from app.models.session import Session
from app.models.participant import Participant
from app.models.category import CategoryOption
from app.schemas.session import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionOut,
    SessionStateResponse,
)
from app.constants import (
    NEXT_STATE,
    SessionState,
)
from app.utils.urls import FRONTEND_URL, URLPath
from app.utils.http import HTTPStatusCode, HTTPErrorMessage
from app.services.ai_service import AIService


class SessionService:
    @staticmethod
    def create(
        db: DBSession,
        body: CreateSessionRequest,
        background_tasks: BackgroundTasks,
    ) -> CreateSessionResponse:
        session = Session(
            topic=body.topic,
            context=body.context,
            expected_count=body.expected_count,
        )
        db.add(session)
        db.flush()

        host = Participant(
            session_id=session.id,
            display_name=body.host_display_name,
        )
        db.add(host)
        db.flush()

        session.host_id = host.id
        db.commit()

        background_tasks.add_task(
            AIService.generate_questions,
            str(session.id),
            body.topic,
            body.context,
            body.host_notes,
        )

        return CreateSessionResponse(
            session_id=str(session.id),
            host_participant_id=str(host.id),
            join_link=f"{FRONTEND_URL}{URLPath.JOIN_SESSION}/{session.id}",
        )

    @staticmethod
    def get(
        db: DBSession,
        session_id: str
    ) -> SessionOut:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        return SessionOut(
            id=str(session.id),
            topic=session.topic,
            context=session.context,
            state=session.state,
            expected_count=session.expected_count,
            answered_count=session.answered_count,
            created_at=session.created_at,
        )

    @staticmethod
    def get_state(
        db: DBSession,
        session_id: str
    ) -> SessionStateResponse:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        
        categories_ready = (
            db.query(CategoryOption).filter(CategoryOption.session_id == _uuid.UUID(session_id)).first()
            is not None
        )

        return SessionStateResponse(
            state=session.state,
            participants_answered=session.answered_count,
            expected=session.expected_count,
            categories_ready=categories_ready,
        )

    @staticmethod
    def advance_state(
        db: DBSession,
        session_id: str,
        participant_id: str,
        background_tasks: BackgroundTasks,
    ) -> SessionStateResponse:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        
        if str(session.host_id) != participant_id:
            raise HTTPException(
                status_code=HTTPStatusCode.FORBIDDEN,
                detail=HTTPErrorMessage.ONLY_HOST_CAN_ADVANCE,
            )
        
        next_state = NEXT_STATE.get(session.state)
        if not next_state:
            raise HTTPException(
                status_code=HTTPStatusCode.BAD_REQUEST,
                detail=HTTPErrorMessage.CANNOT_ADVANCE_FROM_STATE,
            )

        session.state = next_state
        db.commit()
        
        if next_state == SessionState.GENERATING:
            background_tasks.add_task(AIService.generate_categories, str(session.id))

        categories_ready = (
            db.query(CategoryOption).filter(CategoryOption.session_id == _uuid.UUID(session_id)).first()
            is not None
        )
        
        return SessionStateResponse(
            state=session.state,
            participants_answered=session.answered_count,
            expected=session.expected_count,
            categories_ready=categories_ready,
        )

    @staticmethod
    def advance_session_to_state(
        db: DBSession,
        session_id: str,
        state: SessionState
    ):
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        
        session.state = state
        db.commit()