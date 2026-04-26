"""Phase 2 pipeline: collect -> normalize -> validate preference input."""

from __future__ import annotations

from typing import Any

from normalizer import normalize_raw_input
from schema import UserPreferences


def run_phase2(raw_input: dict[str, Any]) -> tuple[UserPreferences, dict[str, Any]]:
    """Execute Phase 2 and return (validated preferences, report)."""
    normalized = normalize_raw_input(raw_input)
    validated = UserPreferences.model_validate(normalized)
    report: dict[str, Any] = {
        "input_keys": sorted(list(raw_input.keys())),
        "normalized": normalized,
        "valid": True,
    }
    return validated, report
