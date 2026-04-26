"""Formatting helpers for Phase 4 outputs."""

from __future__ import annotations

from schema import LLMResponse


def to_display_rows(response: LLMResponse) -> list[dict]:
    rows: list[dict] = []
    for r in response.recommendations:
        rows.append(
            {
                "rank": r.rank,
                "restaurant_name": r.restaurant_name,
                "cuisine": r.cuisine,
                "rating": r.rating,
                "cost_for_two": r.cost_for_two,
                "explanation": r.explanation,
            }
        )
    return rows
