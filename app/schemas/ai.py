from app.constants import Mechanic


class AIQuestion:
    text: str
    mechanic: Mechanic
    options: list[str]
    display_order: int


class AIQuestionsResponse:
    valid: bool
    questions: list[AIQuestion]


class AIResult:
    name: str
    reasoning: str


class AIResultsResponse:
    valid: bool
    results: list[AIResult]
