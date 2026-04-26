"""Phase 3 pipeline: load cleaned data + preferences -> shortlist candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine import apply_hard_filters, rank_candidates
from schema import Candidate, RestaurantRecord, UserPreferences


def load_restaurants_from_jsonl(path: str | Path) -> list[RestaurantRecord]:
    rows: list[RestaurantRecord] = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(RestaurantRecord.model_validate(json.loads(line)))
    return rows


def run_phase3(
    restaurants: list[RestaurantRecord],
    preferences_payload: dict[str, Any],
    top_n: int = 20,
) -> tuple[list[Candidate], dict[str, Any]]:
    prefs = UserPreferences.model_validate(preferences_payload)
    filtered = apply_hard_filters(restaurants, prefs)
    ranked = rank_candidates(filtered, prefs, top_n=top_n)

    report: dict[str, Any] = {
        "input_restaurants": len(restaurants),
        "after_hard_filters": len(filtered),
        "output_candidates": len(ranked),
        "top_n": top_n,
    }
    return ranked, report
