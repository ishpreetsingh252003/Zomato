"""Phase 3 pipeline: load cleaned data + preferences -> shortlist candidates."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from engine import apply_hard_filters, rank_candidates
from schema import Candidate, RestaurantRecord, UserPreferences


def load_restaurants_from_jsonl(path: str | Path) -> list[RestaurantRecord]:
    rows: list[RestaurantRecord] = []
    p = Path(path)
    opener = gzip.open if p.suffix == ".gz" else p.open
    with opener(p, "rt", encoding="utf-8") as f:
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
    
    # Deduplicate restaurants by name and location to avoid duplicates in results
    seen_restaurants = set()
    deduplicated_restaurants = []
    for r in filtered:
        restaurant_key = (r.restaurant_name.lower().strip(), r.location.lower().strip())
        if restaurant_key not in seen_restaurants:
            seen_restaurants.add(restaurant_key)
            deduplicated_restaurants.append(r)
    
    ranked = rank_candidates(deduplicated_restaurants, prefs, top_n=top_n)

    report: dict[str, Any] = {
        "input_restaurants": len(restaurants),
        "after_hard_filters": len(filtered),
        "after_deduplication": len(deduplicated_restaurants),
        "output_candidates": len(ranked),
        "top_n": top_n,
    }
    return ranked, report
