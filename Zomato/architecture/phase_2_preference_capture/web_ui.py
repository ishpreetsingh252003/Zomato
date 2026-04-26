"""Basic web UI for Phase 2 preference capture."""

from __future__ import annotations

import traceback

from flask import Flask, render_template, request

from pipeline import run_phase2

app = Flask(__name__, template_folder="templates")


@app.get("/")
def index():
    return render_template("index.html", result=None, report=None, error=None)


@app.post("/capture")
def capture():
    raw = {
        "location": request.form.get("location", ""),
        "budget": request.form.get("budget", ""),
        "cuisines": request.form.get("cuisines", ""),
        "min_rating": request.form.get("min_rating", ""),
        "optional_preferences": request.form.get("optional_preferences", ""),
        "free_text": request.form.get("free_text", ""),
    }
    try:
        prefs, report = run_phase2(raw)
        return render_template(
            "index.html",
            result=prefs.model_dump(),
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
    app.run(host="127.0.0.1", port=5001, debug=False)


if __name__ == "__main__":
    main()
