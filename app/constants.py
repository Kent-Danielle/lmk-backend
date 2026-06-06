from enum import Enum


class SessionState(str, Enum):
    ANSWERING  = "ANSWERING"
    GENERATING = "GENERATING"
    RESULTS    = "RESULTS"


class Mechanic(str, Enum):
    MULTISELECT = "MULTISELECT"
    SLIDER = "SLIDER"
    TEXT = "TEXT"
    SWIPE = "SWIPE"
    NUMBER = "NUMBER"
    


class ResultType(str, Enum):
    RECOMMENDATION = "RECOMMENDATION"
    OVERALL = "OVERALL"


# Controls the display order of result types in GET /results.
# Change the list order here to reorder how types appear to clients.
RESULT_TYPE_ORDER: list[ResultType] = [
    ResultType.OVERALL,
    ResultType.RECOMMENDATION,
]


NEXT_STATE = {
    SessionState.ANSWERING:  SessionState.GENERATING,
    SessionState.GENERATING: SessionState.RESULTS
}


AI_TIMEOUT_SECONDS = 30
AI_MAX_RETRIES = 2

AI_MIN_QUESTIONS = 5
AI_MAX_QUESTIONS = 10