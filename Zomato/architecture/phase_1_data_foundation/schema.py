"""Standard restaurant record schema for Phase 1 (Data Foundation)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class RestaurantRecord(BaseModel):
    """Normalized, queryable row after preprocessing."""

    restaurant_name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    cuisine: str = Field(..., min_length=1)
    cost_for_two: float | None = Field(
        default=None,
        description="Approximate cost for two in local currency, if known.",
    )
    rating: float | None = Field(
        default=None,
        ge=0.0,
        le=5.0,
        description="Aggregate rating on 0–5 scale, if known.",
    )
    extras: dict[str, Any] = Field(
        default_factory=dict,
        description="Other raw/normalized attributes preserved for downstream phases.",
    )

    @field_validator("restaurant_name", "location", "cuisine", mode="before")
    @classmethod
    def strip_strings(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    model_config = {"extra": "forbid"}


def validate_records(rows: list[dict[str, Any]]) -> tuple[list[RestaurantRecord], list[str]]:
    """
    Validate a list of dicts against RestaurantRecord.
    Returns (valid_records, error_messages for invalid rows).
    """
    valid: list[RestaurantRecord] = []
    errors: list[str] = []
    for i, row in enumerate(rows):
        try:
            valid.append(RestaurantRecord.model_validate(row))
        except Exception as e:  # noqa: BLE001 — collect all validation errors
            errors.append(f"row {i}: {e}")
    return valid, errors
