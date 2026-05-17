"""Training value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingPriority:
    value: str

