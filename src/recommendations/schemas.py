from pydantic import BaseModel

from src.constants import SuppressionReason, TriggerReason


class Decision(BaseModel):
    fired: bool
    trigger_reason: TriggerReason | None = None
    suppression_reason: SuppressionReason | None = None
    profile_hash: str
    catalog_version: str
    events_considered: int


class Efficiency(BaseModel):
    events_recorded: int
    decisions: int
    fired: int
    suppressed: int
    cache_hit_ratio: float
    llm_calls: int
    calls_per_event: float
    last_trigger: TriggerReason | None = None
    last_suppression: SuppressionReason | None = None
