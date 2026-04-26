"""Basic web UI for Phase 3 candidate retrieval."""

from __future__ import annotations

import traceback

from flask import Flask, render_template, request

from pipeline import load_restaurants_from_jsonl, run_phase3

app = Flask(__name__, template_folder="templates")


@app.get("/")
def index():
    return render_template("index.html", result=None, report=None, error=None)


@app.post("/retrieve")
def retrieve():
    dataset_path = request.form.get("dataset_path", "").strip()
    raw = {
        "location": request.form.get("location", ""),
        "budget": request.form.get("budget", "medium"),
        "cuisines": [x.strip() for x in request.form.get("cuisines", "").split(",") if x.strip()],
        "min_rating": request.form.get("min_rating", "0"),
        "optional_preferences": [
            x.strip().lower()
            for x in request.form.get("optional_preferences", "").split(",")
            if x.strip()
        ],
    }
    top_n = int(request.form.get("top_n", "20") or "20")
    try:
        restaurants = load_restaurants_from_jsonl(dataset_path)
        candidates, report = run_phase3(restaurants, raw, top_n=top_n)
        return render_template(
            "index.html",
            result=[c.model_dump() for c in candidates],
            report=report,
            error=None,
        )
    except Exception:
        return render_template(
            "index.html",
            result=None,
            report=None,
            error=traceback.format_exc(),
        ), 400


def main() -> None:
    app.run(host="127.0.0.1", port=5002, debug=False)


if __name__ == "__main__":
    main()
