from fastapi import FastAPI

from app.middleware.cors import add_cors
from app.routers import sessions, participants, answers, swipes

app = FastAPI(title="lmk API")

add_cors(app)

app.include_router(sessions.router)
app.include_router(participants.router)
app.include_router(answers.router)
app.include_router(swipes.router)


@app.get("/")
async def root():
    return {"status": "ok"}
