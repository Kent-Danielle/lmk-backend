import logging

from fastapi import FastAPI

from app.middleware.cors import add_cors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
from app.routers import sessions, participants, answers
from app.utils.http import HTTPStatusCode

app = FastAPI(title="lmk API")

add_cors(app)

app.include_router(sessions.router)
app.include_router(participants.router)
app.include_router(answers.router)


@app.get("/", status_code=HTTPStatusCode.OK)
async def root():
    return {"status": "ok"}
