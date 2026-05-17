"""Pressure API DTO placeholder."""

from pydantic import BaseModel


class PressureSessionResponse(BaseModel):
    session_id: str
    status: str

