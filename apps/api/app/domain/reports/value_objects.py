"""Report value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CopyBoundary:
    allows_file_artifact: bool = False

