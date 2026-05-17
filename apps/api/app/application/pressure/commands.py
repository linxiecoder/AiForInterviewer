"""Pressure commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreatePressureQuestionTaskCommand:
    session_id: str

