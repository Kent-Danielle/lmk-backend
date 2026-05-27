from enum import Enum


# HTTP Status Codes
class HTTPStatusCode(int, Enum):
    OK = 200
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    NOT_IMPLEMENTED = 501


# HTTP Response Messages
class HTTPErrorMessage(str, Enum):
    SESSION_NOT_FOUND = "Session not found."
    DISPLAY_NAME_TAKEN = "Display name already taken in this session."
    ONLY_HOST_CAN_ADVANCE = "Only the host can advance."
    CANNOT_ADVANCE_FROM_STATE = "Cannot advance from this state"
    NOT_IMPLEMENTED = "Not implemented"
    QUESTIONS_NOT_READY = "Questions are still being generated. Please try again shortly."
    QUESTIONS_GENERATION_FAILED = "Question generation failed. Please create a new session."
