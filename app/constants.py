from enum import Enum


class SessionState(str, Enum):
    QUESTION_PHASE = "QUESTION_PHASE"
    WAITING = "WAITING"
    REVEAL = "REVEAL"
    SWIPE_PHASE = "SWIPE_PHASE"
    RESULTS = "RESULTS"


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
    SessionState.WAITING: SessionState.REVEAL,
    SessionState.REVEAL: SessionState.SWIPE_PHASE,
    SessionState.SWIPE_PHASE: SessionState.RESULTS,
}
