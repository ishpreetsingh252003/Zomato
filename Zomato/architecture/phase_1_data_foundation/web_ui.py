"""Basic web UI: submit form → download HF dataset → run Phase 1 pipeline."""

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory, url_for

from data_loader import DEFAULT_HF_DATASET
from pipeline import records_to_jsonl, run_phase1, write_report

APP_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = APP_ROOT / "output"

app = Flask(__name__, template_folder=str(APP_ROOT / "templates"))
app.config["MAX_CONTENT_LENGTH"] = 1_000_000


@app.route("/")
def index():
    return render_template(
        "index.html",
        default_dataset_id=DEFAULT_HF_DATASET,
        report=None,
        error=None,
        preview_rows=None,
        output_files=None,
    )


@app.post("/run-phase1")
def run_phase1_route():
    dataset_id = (request.form.get("dataset_id") or "").strip() or DEFAULT_HF_DATASET
    split = (request.form.get("split") or "train").strip()
    max_raw = (request.form.get("max_rows") or "").strip()
    max_rows: int | None = None
    if max_raw:
        try:
            max_rows = int(max_raw)
            if max_rows < 1:
                raise ValueError("max_rows must be >= 1")
        except ValueError as e:
            return render_template(
                "index.html",
                default_dataset_id=dataset_id,
                report=None,
                error=f"Invalid max rows: {e}",
                preview_rows=None,
                output_files=None,
            ), 400

    save_outputs = request.form.get("save_outputs") == "1"

    try:
        records, report = run_phase1(
            source="huggingface",
            path=None,
            dataset_id=dataset_id,
            split=split,
            max_rows=max_rows,
        )
    except Exception:  # noqa: BLE001 — show full error in dev UI
        tb = traceback.format_exc()
        return render_template(
            "index.html",
            default_dataset_id=dataset_id,
            report=None,
            error=tb,
            preview_rows=None,
            output_files=None,
        ), 500

    output_files: list[Path] = []
    if save_outputs:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base = f"phase1_{ts}"
        jsonl_path = OUTPUT_DIR / f"{base}.jsonl"
        report_path = OUTPUT_DIR / f"{base}_report.json"
        records_to_jsonl(records, jsonl_path)
        write_report(report, report_path)
        output_files = [jsonl_path, report_path]

    preview = [r.model_dump() for r in records[:20]]

    return render_template(
        "index.html",
        default_dataset_id=DEFAULT_HF_DATASET,
        report=report,
        error=None,
        preview_rows=preview,
        output_files=output_files,
    )


@app.route("/download/<path:name>")
def download_file(name: str):
    """Serve files only from OUTPUT_DIR (basename enforced)."""
    safe = Path(name).name
    return send_from_directory(OUTPUT_DIR, safe, as_attachment=True)


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("index"))


def main() -> None:
    # Bind 127.0.0.1 for local dev; change host if needed on LAN
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
