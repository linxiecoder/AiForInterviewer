"""Unit of Work application port."""

from typing import Protocol


class UnitOfWork(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...

