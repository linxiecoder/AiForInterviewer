"""Validation result concepts shared by AI and application modules."""

from dataclasses import dataclass, field

from app.domain.shared.enums import ValidationStatus


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    failure_signals: tuple[str, ...] = field(default_factory=tuple)
    repair_hint: str | None = None

