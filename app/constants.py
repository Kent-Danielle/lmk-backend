from enum import Enum


class SessionState(str, Enum):
    QUESTION_PHASE = "QUESTION_PHASE"
    WAITING = "WAITING"
    REVEAL = "REVEAL"

class Mechanic(str, Enum):
    SWIPE = "SWIPE"
    MULTISELECT = "MULTISELECT"
    SLIDER = "SLIDER"
    TEXT = "TEXT"


class SwipeDirection(str, Enum):
    YES = "YES"
    NO = "NO"


NEXT_STATE = {
    SessionState.QUESTION_PHASE: SessionState.WAITING,
    SessionState.WAITING: SessionState.REVEAL
}


MAX_HOST_NOTES_LENGTH = 500
AI_TIMEOUT_SECONDS = 30
AI_MAX_RETRIES = 2
