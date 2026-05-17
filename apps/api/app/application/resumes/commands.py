"""Resume commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateResumeCommand:
    title: str
    markdown_text: str

