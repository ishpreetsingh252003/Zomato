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

_PHASE5_DIR = Path(__file__).resolve().parents[1]
_SAMPLE_RECS = _PHASE5_DIR / "sample_recommendations.json"


def _load_sample_recommendations() -> dict[str, Any]:
    return json.loads(_SAMPLE_RECS.read_text(encoding="utf-8"))


def _resolve_phase1_dataset_path() -> Path | None:
    """
    Resolve the best available Phase 1 JSONL dataset file.
    Priority:
    1) phase1_live.jsonl (legacy expected name)
    2) newest phase1_*.jsonl in phase_1_data_foundation/output
    """
    output_dir = _ARCH_DIR / "phase_1_data_foundation" / "output"
    preferred = output_dir / "phase1_live.jsonl"
    if preferred.exists():
        return preferred
    candidates = sorted(output_dir.glob("phase1*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    return None


def _load_restaurants(location: str | None = None) -> list[dict]:
    """Load restaurants from full dataset if available, else sample data."""
    # Try the full dataset first
    live_p = _resolve_phase1_dataset_path()
    if live_p and live_p.exists():
        records = []
        
        with open(live_p, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
        
        # Only filter by location if specified, using more flexible matching
        if location:
            location_lower = location.lower().strip()
            filtered_records = []
            for r in records:
                r_location = r.get("location", "").lower().strip()
                if location_lower in r_location or r_location in location_lower:
                    filtered_records.append(r)
            records = filtered_records
        
        return records

    # Fallback to sample
    p = _ARCH_DIR / "phase_3_candidate_retrieval" / "sample_restaurants.jsonl"
    if not p.exists():
        return []

    records = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    # Keep fallback behavior aligned with full dataset path.
    if location:
        location_lower = location.lower().strip()
        records = [
            r
            for r in records
            if location_lower in r.get("location", "").lower().strip()
            or r.get("location", "").lower().strip() in location_lower
        ]
    return records


def get_metadata() -> dict[str, list[str]]:
    """Return precomputed metadata, or generate dynamically."""
    meta_p = _PHASE5_DIR / "metadata.json"
    if meta_p.exists():
        return json.loads(meta_p.read_text(encoding="utf-8"))
        
    raw_records = _load_restaurants()
    locations: set[str] = set()
    cuisines: set[str] = set()
    
    for r in raw_records:
        loc = r.get("location")
        if loc:
            locations.add(loc.strip())
        c_list = r.get("cuisine", "")
        if isinstance(c_list, str):
            for c in c_list.split(","):
                c = c.strip()
                if c:
                    cuisines.add(c)
                    
    return {
        "locations": sorted(list(locations)),
        "cuisines": sorted(list(cuisines))
    }


def run_pipeline(preferences: dict[str, Any], top_n: int = 5) -> dict[str, Any]:
    """Run complete pipeline with completely fresh state for each call."""
    """
    Full end-to-end pipeline.

    1. Load restaurant records (Phase 1 output or Phase 3 sample).
    2. Apply Phase 3 hard filters + scoring.
    3. Pass shortlisted candidates to Phase 4 LLM.
    4. Return structured recommendation payload.

    Falls back to sample recommendations when Groq key is missing or dataset
    is not available, so the frontend always has something to render.
    """
    
    # Reset noisy module caches and import Phase 3 deterministically.
    import sys
    import importlib
    import traceback
    import importlib.util as _ilu

    for module_name in ("schema", "engine", "pipeline", "phase_3_pipeline", "phase_4_pipeline", "phase_4_schema"):
        sys.modules.pop(module_name, None)
    importlib.invalidate_caches()

    run_phase3 = None
    load_restaurants_from_jsonl = None
    try:
        p3_dir = str(_ARCH_DIR / "phase_3_candidate_retrieval")
        if p3_dir in sys.path:
            sys.path.remove(p3_dir)
        sys.path.insert(0, p3_dir)

        spec_pipe = _ilu.spec_from_file_location(
            "phase_3_pipeline",
            _ARCH_DIR / "phase_3_candidate_retrieval" / "pipeline.py",
        )
        mod_pipe = _ilu.module_from_spec(spec_pipe)  # type: ignore[arg-type]
        sys.modules["phase_3_pipeline"] = mod_pipe
        spec_pipe.loader.exec_module(mod_pipe)  # type: ignore[union-attr]

        run_phase3 = mod_pipe.run_phase3
        load_restaurants_from_jsonl = mod_pipe.load_restaurants_from_jsonl
    except Exception as e:
        print(f"Phase 3 import failed: {e}")
        traceback.print_exc()

    # ---- Load dataset -------------------------------------------------------
    loc = preferences.get("location")
    raw_records = _load_restaurants(location=loc)
    
    # Debug: Check what we're loading
    print(f"Loading restaurants for location: {loc}")
    print(f"Found {len(raw_records)} records")

    if not raw_records or run_phase3 is None:
        sample = _load_sample_recommendations()
        sample["preferences_used"] = preferences
        return sample

    # ---- Phase 3: filter + rank (with deduplication) -----------------------
    try:
        # Load restaurants from the full dataset and run Phase 3 with deduplication
        dataset_path = _resolve_phase1_dataset_path()
        if dataset_path is None:
            raise FileNotFoundError("No Phase 1 JSONL dataset found in phase_1_data_foundation/output")
        restaurants = load_restaurants_from_jsonl(str(dataset_path))
        candidates, report = run_phase3(restaurants, preferences, top_n=top_n * 3)
        
        # Debug: print what we got
        print(f"Phase 3 processed: {len(restaurants)} -> {len(candidates)} candidates")
            
    except Exception as e:
        print(f"Phase 3 error: {e}")
        import traceback
        traceback.print_exc()
        sample = _load_sample_recommendations()
        sample["source"] = "sample"
        sample["preferences_used"] = preferences
        return sample

    # ---- Phase 4: LLM ranking ----------------------------------------------
    try:
        # Clear all Phase 4 module caches to ensure fresh imports
        modules_to_clear = ['phase_4_pipeline', 'phase_4_schema', 'schema']
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)
        
        # Force fresh import by clearing import cache
        import importlib
        importlib.invalidate_caches()
        
        import importlib.util as _ilu2
        from pathlib import Path as _Path
        import os
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=_PHASE5_DIR / ".env")
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        print(f"Groq API key found: {bool(api_key and api_key.strip())}")
        if not api_key:
            raise RuntimeError("No GROQ_API_KEY")

        p4_dir = str(_ARCH_DIR / "phase_4_llm_recommendation")
        if p4_dir in sys.path:
            sys.path.remove(p4_dir)
        sys.path.insert(0, p4_dir)

        spec_p4 = _ilu2.spec_from_file_location(
            "phase_4_pipeline",
            _ARCH_DIR / "phase_4_llm_recommendation" / "pipeline.py",
        )
        mod_p4 = _ilu2.module_from_spec(spec_p4)  # type: ignore[arg-type]
        sys.modules["phase_4_pipeline"] = mod_p4
        spec_p4.loader.exec_module(mod_p4)  # type: ignore[union-attr]

        spec_s4 = _ilu2.spec_from_file_location(
            "phase_4_schema",
            _ARCH_DIR / "phase_4_llm_recommendation" / "schema.py",
        )
        mod_s4 = _ilu2.module_from_spec(spec_s4)  # type: ignore[arg-type]
        sys.modules["phase_4_schema"] = mod_s4
        spec_s4.loader.exec_module(mod_s4)  # type: ignore[union-attr]

        CandidateInput = mod_s4.CandidateInput
        PreferencesInput = mod_s4.PreferencesInput

        cands4 = [CandidateInput.model_validate(c.model_dump()) for c in candidates]
        prefs4 = PreferencesInput.model_validate(preferences)

        print("Calling Phase 4 LLM API...")
        response, _report = mod_p4.run_phase4(prefs4, cands4, top_n=top_n)
        print("Phase 4 LLM call successful!")

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

    except Exception as e:
        # LLM unavailable — return Phase 3 ranked candidates as recommendations
        print(f"Phase 4 LLM API failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Always return Phase 3 ranked candidates as fallback when LLM fails
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
