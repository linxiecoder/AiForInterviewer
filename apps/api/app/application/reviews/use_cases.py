"""Review use case placeholders."""

from app.application.common.result import ApplicationResult


class ReviewUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="review_skeleton")

