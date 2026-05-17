"""Binding repository ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class BindingRepository(Protocol):
    def get_ref(self, binding_id: str) -> ResourceRef | None: ...

