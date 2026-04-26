"""Schemas for Phase 4 LLM reasoning and recommendation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateInput(BaseModel):
    restaurant_name: str
    location: str
    cuisine: str
    rating: float | None = Field(default=None, ge=0, le=5)
    cost_for_two: float | None = Field(default=None, ge=0)
    score: float | None = None
    match_reasons: list[str] = Field(default_factory=list)


class PreferencesInput(BaseModel):
    location: str
    budget: str
    cuisines: list[str] = Field(default_factory=list)
    min_rating: float = Field(default=0, ge=0, le=5)
    optional_preferences: list[str] = Field(default_factory=list)


class RankedRecommendation(BaseModel):
    rank: int
    restaurant_name: str
    explanation: str
    rating: float | None = Field(default=None, ge=0, le=5)
    cost_for_two: float | None = Field(default=None, ge=0)
    cuisine: str


class LLMResponse(BaseModel):
    summary: str
    recommendations: list[RankedRecommendation]
