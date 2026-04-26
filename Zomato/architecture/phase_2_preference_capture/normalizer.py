"""Normalize raw UI/API input into canonical fields for validation."""

from __future__ import annotations

import re
from typing import Any

_BUDGET_MAP = {
    "cheap": "low",
    "affordable": "low",
    "budget": "low",
    "economy": "low",
    "mid": "medium",
    "moderate": "medium",
    "normal": "medium",
    "premium": "high",
    "expensive": "high",
    "luxury": "high",
}

_OPTIONAL_PATTERNS = {
    "family-friendly": re.compile(r"\bfamily\b", re.IGNORECASE),
    "quick-service": re.compile(r"\bquick\b|\bfast\b", re.IGNORECASE),
    "outdoor-seating": re.compile(r"\boutdoor\b", re.IGNORECASE),
    "vegetarian-options": re.compile(r"\bveg\b|\bvegetarian\b", re.IGNORECASE),
}


def _parse_budget(raw_budget: str, free_text: str) -> str:
    b = raw_budget.strip().lower()
    if b in {"low", "medium", "high"}:
        return b
    if b in _BUDGET_MAP:
        return _BUDGET_MAP[b]

    for word in re.findall(r"[a-zA-Z\-]+", free_text.lower()):
        if word in {"low", "medium", "high"}:
            return word
        if word in _BUDGET_MAP:
            return _BUDGET_MAP[word]
    return "medium"


def _parse_rating(raw_rating: object) -> float:
    s = str(raw_rating or "").strip()
    if not s:
        return 0.0
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return 0.0
    value = float(m.group(1))
    if value < 0:
        return 0.0
    if value > 5:
        return 5.0
    return value


def _parse_optional_preferences(raw_optional: str, free_text: str) -> list[str]:
    explicit = [x.strip().lower() for x in (raw_optional or "").split(",") if x.strip()]
    merged = " ".join(explicit) + " " + free_text
    inferred: list[str] = []
    for name, pattern in _OPTIONAL_PATTERNS.items():
        if pattern.search(merged):
            inferred.append(name)
    # keep explicit first, then inferred unique
    seen: set[str] = set()
    out: list[str] = []
    for item in explicit + inferred:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def normalize_raw_input(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert noisy form/API payload to canonical UserPreferences payload."""
    free_text = str(raw.get("free_text", "") or "").strip()
    cuisines = str(raw.get("cuisines", "") or "")
    optional = str(raw.get("optional_preferences", "") or "")
    budget_raw = str(raw.get("budget", "") or "")

    return {
        "location": str(raw.get("location", "") or "").strip(),
        "budget": _parse_budget(budget_raw, free_text),
        "cuisines": cuisines,
        "min_rating": _parse_rating(raw.get("min_rating", "")),
        "optional_preferences": _parse_optional_preferences(optional, free_text),
        "free_text": free_text,
    }
