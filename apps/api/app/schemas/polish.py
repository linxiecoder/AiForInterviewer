"""Polish API DTO placeholder."""

from pydantic import BaseModel


class PolishSessionResponse(BaseModel):
    session_id: str
    status: str

