from enum import Enum


class SessionState(str, Enum):
    ANSWERING  = "ANSWERING"
    GENERATING = "GENERATING"
    RESULTS    = "RESULTS"

class Mechanic(str, Enum):
    MULTISELECT = "MULTISELECT"
    SLIDER = "SLIDER"
    TEXT = "TEXT"

class ResultType(str, Enum):
    RECOMMENDATION = "RECOMMENDATION"

NEXT_STATE = {
    SessionState.ANSWERING:  SessionState.GENERATING,
    SessionState.GENERATING: SessionState.RESULTS
}


MAX_HOST_NOTES_LENGTH = 500
AI_TIMEOUT_SECONDS = 30
AI_MAX_RETRIES = 2
