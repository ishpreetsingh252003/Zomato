"""Schema for Phase 3 candidate retrieval and filtering."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    location: str = Field(..., min_length=1)
    budget: str = Field(..., pattern="^(low|medium|high)$")
    cuisines: list[str] = Field(default_factory=list)
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    optional_preferences: list[str] = Field(default_factory=list)


class RestaurantRecord(BaseModel):
    restaurant_name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)
    cuisine: str = Field(..., min_length=1)
    cost_for_two: float | None = Field(default=None, ge=0.0)
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    extras: dict[str, Any] = Field(default_factory=dict)


class Candidate(BaseModel):
    restaurant_name: str
    location: str
    cuisine: str
    rating: float | None
    cost_for_two: float | None
    score: float
    match_reasons: list[str] = Field(default_factory=list)
