import json
import uuid as _uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from app.models.result import Result
from app.models.session import Session
from app.schemas.ai import AIResult
from app.schemas.result import ResultOut, ResultsResponse
from app.utils.http import HTTPErrorMessage, HTTPStatusCode


class ResultService:
    @staticmethod
    def save_results(
        db: DBSession, 
        session_id: str, 
        results: list[AIResult]
    ) -> None:
        """Persist generated results to database."""
        try:
            session_uuid = _uuid.UUID(session_id)
            for result in results:
                db.add(
                    Result(
                        session_id=session_uuid,
                        type = result.type,
                        value = result.value,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
    
    @staticmethod
    def get_results(
        db: DBSession,
        session_id: str,
    ) -> ResultsResponse:
        session = db.query(Session).filter(Session.id == _uuid.UUID(session_id)).first()
        if not session:
            raise HTTPException(
                status_code=HTTPStatusCode.NOT_FOUND,
                detail=HTTPErrorMessage.SESSION_NOT_FOUND,
            )
        
        results = db.query(Result).filter(Result.session_id == session.id).all()
    
        return ResultsResponse(
            results=[
                ResultOut(                                                                                                                                       
                    id=str(r.id),                                                                                                                   
                    type=r.type,                                                                                                                    
                    value=json.loads(r.value),                                                                                                      
                )                                                                                                                                   
                for r in results  
            ]
        )