"""Asset use case placeholders."""

from app.application.common.result import ApplicationResult


class AssetUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="asset_skeleton")

