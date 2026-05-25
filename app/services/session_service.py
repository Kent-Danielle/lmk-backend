import os
from sqlalchemy.orm import Session as DBSession
from fastapi import BackgroundTasks, HTTPException

from app.models.swipe import CategoryOption

from app.db import SessionLocal
from app.models.session import Session
from app.models.participant import Participant
from app.schemas.session import CreateSessionRequest, CreateSessionResponse, SessionOut, SessionStateResponse

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


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
            generate_questions,
            str(session.id),
            body.topic,
            body.context,
            body.host_notes,
        )

        return CreateSessionResponse(
            session_id=str(session.id),
            host_participant_id=str(host.id),
            join_link=f"{FRONTEND_URL}/join/{session.id}",
        )

    @staticmethod
    def get(
        db: DBSession,
        session_id: str
    ) -> SessionOut:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
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
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
        
        categories_ready = (
            db.query(CategoryOption).filter(CategoryOption.session_id == session_id).first()
            is not None
        )

        return SessionStateResponse(
            state=session.state,
            participants_answered=session.answered_count,
            expected=session.expected_count,
            categories_ready=categories_ready,
        )

def generate_questions(
    session_id: str,
    topic: str,
    context: str | None,
    host_notes: str | None,
) -> None:
    # TODO: A4 — OpenAI Call 1, validate mechanic order + Other/Any, save to DB
    pass

