"""Clean, normalize, and map raw rows to the standard schema fields."""

from __future__ import annotations

import re
from typing import Any

# Raw column name aliases -> canonical raw key we use internally before building RestaurantRecord
_NAME_KEYS = (
    "restaurant_name",
    "Restaurant Name",
    "name",
    "Name",
    "restaurant",
    "Restaurant",
)
_LOCATION_KEYS = (
    "location",
    "Location",
    "city",
    "City",
    "locality",
    "Locality",
    "area",
    "Area",
)
_CUISINE_KEYS = (
    "cuisines",
    "Cuisines",
    "cuisine",
    "Cuisine",
)
_RATING_KEYS = (
    "aggregate_rating",
    "Aggregate rating",
    "rating",
    "Rating",
    "rate",
    "Rate",
)
_COST_KEYS = (
    "average_cost_for_two",
    "Average Cost for two",
    "cost",
    "Cost",
    "approx_cost",
    "Approx Cost(for two)",
    "average_cost",
    "cost_for_two",
)


def _first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in row and row[k] is not None and str(row[k]).strip() != "":
            return row[k]
    return None


def _parse_rating(raw: Any) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if s in ("", "NAN", "NA", "N/A", "-", "NEW", "NOT RATED"):
        return None
    # "4.2/5" or "4.2"
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    val = float(m.group(1))
    if val > 5.0 and val <= 10.0:
        val = val / 2.0  # rare 10-scale
    if val < 0 or val > 5.0:
        return None
    return val


def _parse_cost(raw: Any) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if s in ("", "NAN", "NA", "N/A", "-"):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", s.replace(",", ""))
    if not m:
        return None
    return float(m.group(1))


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _normalize_cuisine(raw: Any) -> str:
    if raw is None:
        return ""
    s = _normalize_whitespace(str(raw))
    # Common: "Chinese, Italian" -> normalize comma spacing
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        return ""
    # Title-case light: keep acronyms rough
    return ", ".join(p.title() if p.islower() or p.isupper() else p for p in parts)


def _normalize_location(raw: Any) -> str:
    if raw is None:
        return ""
    return _normalize_whitespace(str(raw)).title()


def _normalize_name(raw: Any) -> str:
    if raw is None:
        return ""
    return _normalize_whitespace(str(raw))


def map_raw_row_to_canonical(raw: dict[str, Any]) -> dict[str, Any]:
    """Map heterogeneous HF/local columns into keys expected by to_restaurant_record."""
    name = _first_present(raw, _NAME_KEYS)
    location = _first_present(raw, _LOCATION_KEYS)
    cuisine = _first_present(raw, _CUISINE_KEYS)
    rating_raw = _first_present(raw, _RATING_KEYS)
    cost_raw = _first_present(raw, _COST_KEYS)

    extras: dict[str, Any] = {}
    used: set[str] = set()
    for keys in (_NAME_KEYS, _LOCATION_KEYS, _CUISINE_KEYS, _RATING_KEYS, _COST_KEYS):
        for k in keys:
            used.add(k)
    for k, v in raw.items():
        if k not in used:
            extras[k] = v

    return {
        "_name": name,
        "_location": location,
        "_cuisine": cuisine,
        "_rating_raw": rating_raw,
        "_cost_raw": cost_raw,
        "_extras": extras,
    }


def to_restaurant_record_dict(canonical: dict[str, Any]) -> dict[str, Any] | None:
    """
    Build a dict suitable for RestaurantRecord.model_validate.
    Returns None if mandatory fields are missing after normalization.
    """
    name = _normalize_name(canonical["_name"])
    location = _normalize_location(canonical["_location"])
    cuisine = _normalize_cuisine(canonical["_cuisine"])
    if not name or not location or not cuisine:
        return None

    rating = _parse_rating(canonical["_rating_raw"])
    cost = _parse_cost(canonical["_cost_raw"])

    return {
        "restaurant_name": name,
        "location": location,
        "cuisine": cuisine,
        "cost_for_two": cost,
        "rating": rating,
        "extras": dict(canonical["_extras"]),
    }


def preprocess_rows(raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Full preprocessing pass: map columns, normalize, drop incomplete rows.
    Returns (list of dicts for Pydantic), stats counters.
    """
    stats = {"input": len(raw_rows), "kept": 0, "dropped_incomplete": 0}
    out: list[dict[str, Any]] = []
    for raw in raw_rows:
        c = map_raw_row_to_canonical(raw)
        rec = to_restaurant_record_dict(c)
        if rec is None:
            stats["dropped_incomplete"] += 1
            continue
        out.append(rec)
        stats["kept"] += 1
    return out, stats
