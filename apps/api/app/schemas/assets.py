"""Asset API DTO placeholder."""

from pydantic import BaseModel


class AssetResponse(BaseModel):
    asset_id: str
    status: str

