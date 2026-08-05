from pydantic import BaseModel, Field

from src.constants import EventType
from src.events.constants import MAX_BATCH, MAX_QUERY_LENGTH


class IncomingEvent(BaseModel):
    type: EventType
    product_id: int | None = None
    category: str | None = Field(default=None, max_length=40)
    query: str | None = Field(default=None, max_length=MAX_QUERY_LENGTH)
    dwell_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    path: str | None = Field(default=None, max_length=300)


class EventBatch(BaseModel):
    events: list[IncomingEvent] = Field(min_length=1, max_length=MAX_BATCH)


class Accepted(BaseModel):
    accepted: int
