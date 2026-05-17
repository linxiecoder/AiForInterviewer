"""Weakness use case placeholders."""

from app.application.common.result import ApplicationResult


class WeaknessUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="weakness_skeleton")

