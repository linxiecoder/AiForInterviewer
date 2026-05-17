"""Polish commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreatePolishFeedbackTaskCommand:
    session_id: str
    answer_id: str

