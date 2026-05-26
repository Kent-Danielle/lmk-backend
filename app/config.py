import os
from dotenv import load_dotenv

load_dotenv()

# Required
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set")

# Optional with defaults
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
