"""Review API DTO placeholder."""

from pydantic import BaseModel


class ReviewResponse(BaseModel):
    review_id: str
    status: str

