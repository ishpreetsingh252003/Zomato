"""Filtering and scoring engine for Phase 3."""

from __future__ import annotations

from typing import Iterable

from schema import Candidate, RestaurantRecord, UserPreferences


def _normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _budget_range(budget: str) -> tuple[float | None, float | None]:
    # Cost for two ranges; tune later with feedback.
    if budget == "low":
        return (0.0, 600.0)
    if budget == "medium":
        return (400.0, 1500.0)
    return (1000.0, None)  # high


def apply_hard_filters(
    restaurants: Iterable[RestaurantRecord],
    preferences: UserPreferences,
) -> list[RestaurantRecord]:
    out: list[RestaurantRecord] = []
    pref_loc = _normalize(preferences.location)
    min_cost, max_cost = _budget_range(preferences.budget)

    for r in restaurants:
        loc = _normalize(r.location)
        if pref_loc not in loc and loc not in pref_loc:
            continue

        rating = r.rating if r.rating is not None else 0.0
        if rating < preferences.min_rating:
            continue

        if r.cost_for_two is not None:
            if min_cost is not None and r.cost_for_two < min_cost:
                continue
            if max_cost is not None and r.cost_for_two > max_cost:
                continue
        out.append(r)
    return out


def _split_cuisine(cuisine: str) -> set[str]:
    return {_normalize(x) for x in cuisine.split(",") if _normalize(x)}


def score_restaurant(r: RestaurantRecord, preferences: UserPreferences) -> Candidate:
    score = 0.0
    reasons: list[str] = []

    # Cuisine similarity
    wanted = {_normalize(x) for x in preferences.cuisines if _normalize(x)}
    has = _split_cuisine(r.cuisine)
    overlap = wanted.intersection(has)
    if wanted:
        cuisine_score = (len(overlap) / max(len(wanted), 1)) * 40.0
        score += cuisine_score
        if overlap:
            reasons.append(f"cuisine match: {', '.join(sorted(overlap))}")

    # Optional preference keyword matching in extras/cuisine/name
    blob = " ".join(
        [
            _normalize(r.restaurant_name),
            _normalize(r.cuisine),
            _normalize(str(r.extras)),
        ]
    )
    opt_hits = [p for p in preferences.optional_preferences if _normalize(p) in blob]
    if opt_hits:
        score += min(20.0, 8.0 * len(opt_hits))
        reasons.append(f"optional preference match: {', '.join(opt_hits)}")

    # Rating boost
    if r.rating is not None:
        score += r.rating * 8.0  # max 40
        reasons.append(f"rating {r.rating:.1f}")

    # Budget closeness score
    min_cost, max_cost = _budget_range(preferences.budget)
    if r.cost_for_two is not None:
        if max_cost is None and min_cost is not None:
            proximity = 1.0 if r.cost_for_two >= min_cost else 0.0
        elif min_cost is not None and max_cost is not None:
            center = (min_cost + max_cost) / 2.0
            width = max(1.0, (max_cost - min_cost) / 2.0)
            proximity = max(0.0, 1.0 - abs(r.cost_for_two - center) / width)
        else:
            proximity = 0.5
        score += proximity * 20.0
        reasons.append("budget fit")

    return Candidate(
        restaurant_name=r.restaurant_name,
        location=r.location,
        cuisine=r.cuisine,
        rating=r.rating,
        cost_for_two=r.cost_for_two,
        score=round(score, 2),
        match_reasons=reasons,
    )


def rank_candidates(
    restaurants: list[RestaurantRecord],
    preferences: UserPreferences,
    top_n: int = 20,
) -> list[Candidate]:
    ranked = [score_restaurant(r, preferences) for r in restaurants]
    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked[:top_n]
