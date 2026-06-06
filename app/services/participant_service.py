import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException

from app.models.session import Session
from app.models.participant import Participant
from app.models.answer import Answer
from app.models.question import Question
from app.schemas.participant import JoinSessionRequest, JoinSessionResponse
from app.utils.http import HTTPStatusCode, HTTPErrorMessage
from app.constants import MAX_PARTICIPANTS, SessionState
from app.services.pendo_service import pendo_track

class ParticipantService:
    @staticmethod
    def join_by_link_id(
        db: DBSession,
        link_id: str,
        body: JoinSessionRequest,
    ) -> JoinSessionResponse:
        session = db.query(Session).filter(Session.link_id == link_id).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )

        if session.state == SessionState.RESULTS:
            pendo_track(
                "participant_join_blocked",
                visitor_id="anonymous",
                account_id=str(session.id),
                properties={
                    "session_id": str(session.id),
                    "block_reason": "session_closed",
                    "link_id": link_id,
                },
            )
            raise HTTPException(
                status_code=HTTPStatusCode.FORBIDDEN,
                detail=HTTPErrorMessage.SESSION_CLOSED,
            )

        existing = (
            db.query(Participant)
            .filter(
                Participant.session_id == session.id,
                Participant.display_name == body.display_name,
            )
            .first()
        )
        if existing:
            return JoinSessionResponse(participant_id=str(existing.id), session_id=str(session.id))

        participant_count = (
            db.query(Participant)
            .filter(Participant.session_id == session.id)
            .count()
        )
        if participant_count >= MAX_PARTICIPANTS:
            pendo_track(
                "participant_join_blocked",
                visitor_id="anonymous",
                account_id=str(session.id),
                properties={
                    "session_id": str(session.id),
                    "block_reason": "session_full",
                    "link_id": link_id,
                },
            )
            raise HTTPException(
                status_code=HTTPStatusCode.FORBIDDEN,
                detail=HTTPErrorMessage.SESSION_FULL,
            )

        participant = Participant(
            session_id=session.id,
            display_name=body.display_name,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(participant)
        db.commit()

        pendo_track(
            "participant_joined",
            visitor_id=str(participant.id),
            account_id=str(session.id),
            properties={
                "session_id": str(session.id),
                "participant_id": str(participant.id),
                "is_new_participant": True,
            },
        )

        return JoinSessionResponse(participant_id=str(participant.id), session_id=str(session.id))

    @staticmethod
    def has_answered(
        db: DBSession,
        session_id: str,
        participant_id: str,
    ) -> bool:
        return (
            db.query(Answer)
            .join(Answer.question)
            .filter(
                Question.session_id == _uuid.UUID(session_id),
                Answer.participant_id == _uuid.UUID(participant_id),
            )
            .first()
        ) is not None

    @staticmethod
    def get_all_participants_answered(db: DBSession, session_id: str) -> list:
        participants = (
            db.query(Participant)
            .filter(Participant.session_id == _uuid.UUID(session_id))
            .join(Answer, Answer.participant_id == Participant.id)
            .distinct()
            .all()
        )
        return [{"participant_id": str(p.id), "display_name": p.display_name} for p in participants]