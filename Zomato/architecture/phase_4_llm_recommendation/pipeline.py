"""Phase 4 pipeline: prompt build -> Groq call -> response validation/format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from llm_service import call_groq_json
from prompt_builder import build_prompt
from response_formatter import to_display_rows
from schema import CandidateInput, LLMResponse, PreferencesInput


def load_candidates_json(path: str | Path) -> list[CandidateInput]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Candidates JSON must be a list.")
    return [CandidateInput.model_validate(x) for x in data]


def load_preferences_json(path: str | Path) -> PreferencesInput:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Preferences JSON must be an object.")
    return PreferencesInput.model_validate(data)


def run_phase4(
    preferences: PreferencesInput,
    candidates: list[CandidateInput],
    top_n: int = 5,
    model: str = "llama-3.1-70b-versatile",
) -> tuple[LLMResponse, dict[str, Any]]:
    prompt = build_prompt(preferences, candidates, top_n=top_n)
    response = call_groq_json(prompt, model=model)
    display_rows = to_display_rows(response)
    report: dict[str, Any] = {
        "candidate_count": len(candidates),
        "returned_count": len(response.recommendations),
        "model": model,
        "top_n_requested": top_n,
        "summary": response.summary,
        "preview": display_rows[:3],
    }
    return response, report
