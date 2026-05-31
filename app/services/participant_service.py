import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException

from app.models.session import Session
from app.models.participant import Participant
from app.schemas.participant import JoinSessionRequest, JoinSessionResponse
from app.utils.http import HTTPStatusCode, HTTPErrorMessage


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

        existing = (
            db.query(Participant)
            .filter(
                Participant.session_id == session.id,
                Participant.display_name == body.display_name,
            )
            .first()
        )
        if existing:
            return JoinSessionResponse(participant_id=str(existing.id))

        participant = Participant(
            session_id=session.id,
            display_name=body.display_name,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(participant)
        db.commit()

        return JoinSessionResponse(participant_id=str(participant.id))
