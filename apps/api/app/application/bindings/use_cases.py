"""Binding use case placeholders."""

from app.application.common.result import ApplicationResult


class BindingUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="binding_skeleton")

