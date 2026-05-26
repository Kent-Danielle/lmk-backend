from enum import Enum

from app.config import FRONTEND_URL


class URLPath(str, Enum):
    JOIN_SESSION = "/join"


CORS_ORIGINS = list(dict.fromkeys([
    FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]))
