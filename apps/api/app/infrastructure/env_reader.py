from __future__ import annotations

from collections.abc import Mapping
import os

_TRUTHY = frozenset({"1", "true", "yes", "on", "y"})
_FALSY = frozenset({"0", "false", "no", "off", "n"})


class EnvReader:
    def __init__(self, values: Mapping[str, str] | None = None):
        self._values = values if values is not None else os.environ

    def optional(self, name: str) -> str | None:
        value = self._values.get(name)
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def str(self, name: str, default: str) -> str:
        value = self.optional(name)
        return value if value is not None else default

    def int(self, name: str, default: int) -> int:
        value = self.optional(name)
        if value is None:
            return default
        try:
            parsed = int(value)
        except ValueError:
            return default
        return parsed if parsed > 0 else default

    def float(self, name: str, default: float) -> float:
        value = self.optional(name)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    def bool(self, name: str, default: bool = False) -> bool:
        value = self.optional(name)
        if value is None:
            return default
        low = value.lower()
        if low in _TRUTHY:
            return True
        if low in _FALSY:
            return False
        return default

    def first_of(self, *names: str) -> str | None:
        for name in names:
            value = self.optional(name)
            if value is not None:
                return value
        return None
