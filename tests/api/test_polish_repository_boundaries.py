"""Phase 1 regression tests for Polish repository dependency direction."""

from __future__ import annotations

import importlib
import inspect


def test_sqlalchemy_polish_repository_does_not_import_application_entities_module() -> None:
    repository_module = importlib.import_module("app.infrastructure.db.repositories.polish")
    source = inspect.getsource(repository_module)

    assert "app.application.polish.entities" not in source
    assert "from app.application.polish.ports import" in source
