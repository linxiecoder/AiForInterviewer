"""Resume commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateResumeCommand:
    owner_id: str
    title: str
    markdown_text: str
