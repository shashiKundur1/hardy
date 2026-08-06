from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.constants import CATEGORIES, Ownership


class ProductWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    brand: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    category: str
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    expected_life_years: int = Field(gt=0, le=200)
    ownership_type: Ownership = Ownership.UNKNOWN
    ownership_since: date | None = None
    ownership_note: str | None = None
    evidence_source: str | None = None
    repairability_score: float | None = Field(default=None, ge=0, le=10)
    parts_until: int | None = None
    warranty: str | None = Field(default=None, max_length=120)
    image_url: str | None = None

    @field_validator("category")
    @classmethod
    def known_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"Unknown category. Use one of: {', '.join(CATEGORIES)}")
        return value

    @model_validator(mode="after")
    def ownership_claim_needs_a_source(self) -> "ProductWrite":
        if self.ownership_type is not Ownership.UNKNOWN and not self.evidence_source:
            raise ValueError(
                "An ownership claim needs an evidence_source. "
                "Leave ownership_type as unknown when there is no source."
            )
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    brand: str
    category: str
    price: Decimal
    currency: str
    expected_life_years: int
    cost_per_year: Decimal
    ownership_type: str
    evidence_source: str | None
    vector_synced_at: datetime | None


class Consistency(BaseModel):
    sqlite_count: int
    qdrant_count: int
    missing_from_qdrant: list[int]
    orphaned_in_qdrant: list[int]
    never_synced: int
    in_sync: bool
