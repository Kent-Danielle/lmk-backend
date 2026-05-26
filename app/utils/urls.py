import os
from enum import Enum


# URL Paths
class URLPath(str, Enum):
    JOIN_SESSION = "/join"


# Environment & Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
