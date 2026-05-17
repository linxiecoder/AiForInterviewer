"""Pressure use case placeholders."""

from app.application.common.result import ApplicationResult


class PressureUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="pressure_skeleton")

