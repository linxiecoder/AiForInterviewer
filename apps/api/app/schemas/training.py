"""Training API DTO placeholder."""

from pydantic import BaseModel


class TrainingSuggestionResponse(BaseModel):
    training_recommendation_id: str
    status: str

