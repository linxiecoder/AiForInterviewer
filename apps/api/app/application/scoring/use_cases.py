"""Scoring use case placeholders."""

from app.application.common.result import ApplicationResult


class ScoringUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="scoring_skeleton")

