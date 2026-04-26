"""Orchestrator for Phase 5: chains Phase 3 filtering + Phase 4 LLM ranking."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path gymnastics so we can import sibling phase packages directly
# ---------------------------------------------------------------------------
_ARCH_DIR = Path(__file__).resolve().parents[2]  # architecture/
sys.path.insert(0, str(_ARCH_DIR / "phase_3_candidate_retrieval"))
sys.path.insert(0, str(_ARCH_DIR / "phase_4_llm_recommendation"))

_PHASE5_DIR = Path(__file__).resolve().parents[1]
_SAMPLE_RECS = _PHASE5_DIR / "sample_recommendations.json"


def _load_sample_recommendations() -> dict[str, Any]:
    return json.loads(_SAMPLE_RECS.read_text(encoding="utf-8"))


def _load_sample_restaurants() -> list[dict]:
    """Load the sample restaurants from Phase 3 sample data."""
    p = _ARCH_DIR / "phase_3_candidate_retrieval" / "sample_restaurants.jsonl"
    if not p.exists():
        return []
    records = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def run_pipeline(preferences: dict[str, Any], top_n: int = 5) -> dict[str, Any]:
    """
    Full end-to-end pipeline.

    1. Load restaurant records (Phase 1 output or Phase 3 sample).
    2. Apply Phase 3 hard filters + scoring.
    3. Pass shortlisted candidates to Phase 4 LLM.
    4. Return structured recommendation payload.

    Falls back to sample recommendations when Groq key is missing or dataset
    is not available, so the frontend always has something to render.
    """
    try:
        from phase_3_schema import UserPreferences, RestaurantRecord  # type: ignore[import]
    except ModuleNotFoundError:
        # Rename import to avoid collision
        import importlib, importlib.util
        spec3 = importlib.util.spec_from_file_location(
            "phase_3_schema",
            _ARCH_DIR / "phase_3_candidate_retrieval" / "schema.py",
        )
        mod3 = importlib.util.module_from_spec(spec3)  # type: ignore[arg-type]
        spec3.loader.exec_module(mod3)  # type: ignore[union-attr]
        UserPreferences = mod3.UserPreferences
        RestaurantRecord = mod3.RestaurantRecord

    try:
        import importlib.util as _ilu

        spec_eng = _ilu.spec_from_file_location(
            "phase_3_engine",
            _ARCH_DIR / "phase_3_candidate_retrieval" / "engine.py",
        )
        mod_eng = _ilu.module_from_spec(spec_eng)  # type: ignore[arg-type]
        spec_eng.loader.exec_module(mod_eng)  # type: ignore[union-attr]
        apply_hard_filters = mod_eng.apply_hard_filters
        rank_candidates = mod_eng.rank_candidates
    except Exception:
        apply_hard_filters = None
        rank_candidates = None

    # ---- Load dataset -------------------------------------------------------
    raw_records = _load_sample_restaurants()

    if not raw_records or apply_hard_filters is None or rank_candidates is None:
        sample = _load_sample_recommendations()
        sample["source"] = "sample"
        sample["preferences_used"] = preferences
        return sample

    # ---- Phase 3: filter + rank --------------------------------------------
    try:
        prefs3 = UserPreferences.model_validate(preferences)
        restaurants = [RestaurantRecord.model_validate(r) for r in raw_records]
        filtered = apply_hard_filters(restaurants, prefs3)
        if not filtered:
            # relax: return all scored
            filtered = restaurants
        candidates = rank_candidates(filtered, prefs3, top_n=top_n * 3)
    except Exception:
        sample = _load_sample_recommendations()
        sample["source"] = "sample"
        sample["preferences_used"] = preferences
        return sample

    # ---- Phase 4: LLM ranking ----------------------------------------------
    try:
        import importlib.util as _ilu2
        from pathlib import Path as _Path
        import os
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=_PHASE5_DIR / ".env")
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("No GROQ_API_KEY")

        spec_p4 = _ilu2.spec_from_file_location(
            "phase_4_pipeline",
            _ARCH_DIR / "phase_4_llm_recommendation" / "pipeline.py",
        )
        mod_p4 = _ilu2.module_from_spec(spec_p4)  # type: ignore[arg-type]
        # inject sibling modules into its namespace
        sys.path.insert(0, str(_ARCH_DIR / "phase_4_llm_recommendation"))
        spec_p4.loader.exec_module(mod_p4)  # type: ignore[union-attr]

        spec_s4 = _ilu2.spec_from_file_location(
            "phase_4_schema",
            _ARCH_DIR / "phase_4_llm_recommendation" / "schema.py",
        )
        mod_s4 = _ilu2.module_from_spec(spec_s4)  # type: ignore[arg-type]
        spec_s4.loader.exec_module(mod_s4)  # type: ignore[union-attr]

        CandidateInput = mod_s4.CandidateInput
        PreferencesInput = mod_s4.PreferencesInput

        cands4 = [CandidateInput.model_validate(c.model_dump()) for c in candidates]
        prefs4 = PreferencesInput.model_validate(preferences)

        response, _report = mod_p4.run_phase4(prefs4, cands4, top_n=top_n)

        recs = []
        for r in response.recommendations:
            recs.append(
                {
                    "rank": r.rank,
                    "restaurant_name": r.restaurant_name,
                    "explanation": r.explanation,
                    "rating": r.rating,
                    "cost_for_two": r.cost_for_two,
                    "cuisine": r.cuisine,
                }
            )

        return {
            "summary": response.summary,
            "recommendations": recs,
            "preferences_used": preferences,
            "source": "live",
        }

    except Exception:
        # LLM unavailable — return Phase 3 ranked candidates as recommendations
        recs = []
        for i, c in enumerate(candidates[:top_n], start=1):
            reasons = ", ".join(c.match_reasons) if c.match_reasons else "Strong overall match"
            recs.append(
                {
                    "rank": i,
                    "restaurant_name": c.restaurant_name,
                    "explanation": f"Ranked #{i} based on your preferences. Match factors: {reasons}.",
                    "rating": c.rating,
                    "cost_for_two": c.cost_for_two,
                    "cuisine": c.cuisine,
                }
            )
        return {
            "summary": f"Top {len(recs)} restaurants matching your preferences in {preferences.get('location','your area')}.",
            "recommendations": recs,
            "preferences_used": preferences,
            "source": "phase3_only",
        }
