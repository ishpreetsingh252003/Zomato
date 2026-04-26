"""Phase 2 schema: structured user preference object."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class UserPreferences(BaseModel):
    """Validated preference object produced by Phase 2."""

    location: str = Field(..., min_length=1)
    budget: str = Field(..., description="One of: low, medium, high")
    cuisines: list[str] = Field(default_factory=list)
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    optional_preferences: list[str] = Field(default_factory=list)
    free_text: str = Field(default="")

    @field_validator("location", mode="before")
    @classmethod
    def clean_location(cls, v: object) -> str:
        return str(v or "").strip().title()

    @field_validator("budget", mode="before")
    @classmethod
    def normalize_budget(cls, v: object) -> str:
        s = str(v or "").strip().lower()
        if s in {"low", "medium", "high"}:
            return s
        raise ValueError("budget must be one of: low, medium, high")

    @field_validator("cuisines", mode="before")
    @classmethod
    def normalize_cuisines(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            raw_items = [x.strip() for x in v.split(",") if x.strip()]
        else:
            raw_items = [str(x).strip() for x in v if str(x).strip()]
        seen: set[str] = set()
        out: list[str] = []
        for item in raw_items:
            normalized = item.title()
            key = normalized.lower()
            if key not in seen:
                seen.add(key)
                out.append(normalized)
        return out

    @field_validator("optional_preferences", mode="before")
    @classmethod
    def normalize_optional_preferences(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            raw_items = [x.strip() for x in v.split(",") if x.strip()]
        else:
            raw_items = [str(x).strip() for x in v if str(x).strip()]
        seen: set[str] = set()
        out: list[str] = []
        for item in raw_items:
            normalized = item.lower()
            if normalized not in seen:
                seen.add(normalized)
                out.append(normalized)
        return out

    @field_validator("free_text", mode="before")
    @classmethod
    def clean_free_text(cls, v: object) -> str:
        return str(v or "").strip()
