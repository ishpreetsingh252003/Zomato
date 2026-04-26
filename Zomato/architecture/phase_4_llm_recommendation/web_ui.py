"""Basic web UI for Phase 4 Groq recommendation generation."""

from __future__ import annotations

import json
import traceback

from flask import Flask, render_template, request

from pipeline import run_phase4
from schema import CandidateInput, PreferencesInput

app = Flask(__name__, template_folder="templates")


def _parse_candidates(text: str) -> list[CandidateInput]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Candidates payload must be a JSON array.")
    return [CandidateInput.model_validate(x) for x in data]


def _parse_preferences(text: str) -> PreferencesInput:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Preferences payload must be a JSON object.")
    return PreferencesInput.model_validate(data)


@app.get("/")
def index():
    return render_template(
        "index.html",
        result=None,
        report=None,
        error=None,
        default_preferences=json.dumps(
            {
                "location": "Bangalore",
                "budget": "medium",
                "cuisines": ["Italian", "Chinese"],
                "min_rating": 4.0,
                "optional_preferences": ["quick-service"],
            },
            indent=2,
        ),
        default_candidates=json.dumps(
            [
                {
                    "restaurant_name": "Pasta Point",
                    "location": "Bangalore",
                    "cuisine": "Italian, Continental",
                    "rating": 4.4,
                    "cost_for_two": 1200,
                    "score": 74.11,
                    "match_reasons": ["cuisine match: italian", "budget fit"],
                },
                {
                    "restaurant_name": "Dragon Wok",
                    "location": "Bangalore",
                    "cuisine": "Chinese, Thai",
                    "rating": 4.2,
                    "cost_for_two": 800,
                    "score": 76.15,
                    "match_reasons": ["cuisine match: chinese", "budget fit"],
                },
            ],
            indent=2,
        ),
    )


@app.post("/recommend")
def recommend():
    model = request.form.get("model", "llama-3.3-70b-versatile").strip()
    top_n = int(request.form.get("top_n", "5"))
    prefs_text = request.form.get("preferences_json", "")
    candidates_text = request.form.get("candidates_json", "")
    try:
        prefs = _parse_preferences(prefs_text)
        candidates = _parse_candidates(candidates_text)
        response, report = run_phase4(prefs, candidates, top_n=top_n, model=model)
        return render_template(
            "index.html",
            result=response.model_dump(),
            report=report,
            error=None,
            default_preferences=prefs_text,
            default_candidates=candidates_text,
        )
    except Exception:
        return render_template(
            "index.html",
            result=None,
            report=None,
            error=traceback.format_exc(),
            default_preferences=prefs_text,
            default_candidates=candidates_text,
        ), 400


def main() -> None:
    app.run(host="127.0.0.1", port=5003, debug=False)


if __name__ == "__main__":
    main()
