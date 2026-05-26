from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.urls import CORS_ORIGINS


def add_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
