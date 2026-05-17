"""Resume value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResumeMarkdown:
    markdown_text: str

