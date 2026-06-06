import secrets
import uuid as _uuid

from sqlalchemy.orm import Session as DBSession
from fastapi import BackgroundTasks, HTTPException
from app.models.session import Session
from app.models.participant import Participant
from app.models.question import Question
from app.models.result import Result
from app.schemas.session import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionInfoResponse,
    SessionStateResponse,
)
from app.constants import (
    NEXT_STATE,
    SessionState,
)
from app.services.event_manager import event_manager
from app.utils.urls import FRONTEND_URL, URLPath
from app.utils.http import HTTPStatusCode, HTTPErrorMessage
from app.services.ai_service import AIService
from app.services.pendo_service import pendo_track


class SessionService:
    @staticmethod
    def create(
        db: DBSession,
        body: CreateSessionRequest,
    ) -> CreateSessionResponse:
        session = Session(
            topic=body.topic,
            context=body.context,
            link_id=secrets.token_urlsafe(7),
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

        success = AIService.generate_questions(
            str(session.id),
            body.topic,
            body.context,
        )

        if not success:
            pendo_track(
                "session_creation_failed",
                visitor_id=str(host.id),
                account_id=str(session.id),
                properties={
                    "topic": body.topic[:100],
                    "has_context": bool(body.context),
                },
            )
            db.delete(session)
            db.commit()
            raise HTTPException(
                status_code=HTTPStatusCode.INTERNAL_SERVER_ERROR,
                detail=HTTPErrorMessage.QUESTIONS_GENERATION_FAILED,
            )

        questions = db.query(Question).filter(Question.session_id == session.id).all()

        pendo_track(
            "session_created",
            visitor_id=str(host.id),
            account_id=str(session.id),
            properties={
                "session_id": str(session.id),
                "topic": body.topic[:100],
                "has_context": bool(body.context),
                "question_count": len(questions),
                "link_id": session.link_id,
            },
        )

        return CreateSessionResponse(
            session_id=str(session.id),
            host_participant_id=str(host.id),
            join_link=session.link_id,
        )

    @staticmethod
    def get_by_session_id(
        db: DBSession,
        session_id: str
    ) -> SessionInfoResponse:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        return SessionService._get_session_helper(session)
    
    @staticmethod
    def _get_session_helper(
        session: Session
    ) -> SessionInfoResponse:
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        
        return SessionInfoResponse(
            id=str(session.id),
            topic=session.topic,
            context=session.context,
            state=session.state,
            join_link=session.link_id,
            created_at=session.created_at,
            host_id=str(session.host_id),
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
        
        results_ready = (
            db.query(Result).filter(Result.session_id == session).first()
            is not None
        )

        return SessionStateResponse(
            state=session.state,
            results_ready=results_ready,
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

        previous_state = session.state
        session.state = next_state
        db.commit()

        event_manager.publish(session_id, next_state.value)

        if next_state == SessionState.GENERATING:
            pendo_track(
                "session_advanced_to_generating",
                visitor_id=participant_id,
                account_id=session_id,
                properties={
                    "session_id": session_id,
                    "participant_id": participant_id,
                    "previous_state": previous_state.value,
                    "new_state": next_state.value,
                },
            )
            background_tasks.add_task(AIService.generate_results, str(session.id))

        results_ready = (
            db.query(Result).filter(Result.session_id == _uuid.UUID(session_id)).first()
            is not None
        )

        return SessionStateResponse(
            state=session.state,
            results_ready=results_ready,
        )