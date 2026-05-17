"""Weakness API DTO placeholder."""

from pydantic import BaseModel


class WeaknessResponse(BaseModel):
    weakness_id: str
    status: str

