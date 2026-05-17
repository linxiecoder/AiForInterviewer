"""Binding domain ports."""

from typing import Protocol

from app.domain.bindings.entities import ResumeJobBinding


class BindingReader(Protocol):
    def get(self, binding_id: str) -> ResumeJobBinding | None: ...

