"""Phase 1 pipeline: load -> preprocess -> validate -> optional export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_loader import (
    DEFAULT_HF_DATASET,
    DEFAULT_HF_SPLIT,
    load_from_csv,
    load_from_huggingface,
    load_from_json,
    load_from_jsonl,
)
from preprocess import preprocess_rows
from schema import RestaurantRecord, validate_records


def run_phase1(
    *,
    source: str = "huggingface",
    path: str | None = None,
    dataset_id: str = DEFAULT_HF_DATASET,
    split: str = DEFAULT_HF_SPLIT,
    max_rows: int | None = None,
) -> tuple[list[RestaurantRecord], dict[str, Any]]:
    """
    Execute Phase 1 end-to-end.

    source: "huggingface" | "json" | "jsonl" | "csv"
    path: required for json/jsonl/csv
    """
    if source == "huggingface":
        raw = load_from_huggingface(dataset_id, split, streaming=False, max_rows=max_rows)
    elif source == "json":
        if not path:
            raise ValueError("path required for json source")
        raw = load_from_json(path)
        if max_rows is not None:
            raw = raw[:max_rows]
    elif source == "jsonl":
        if not path:
            raise ValueError("path required for jsonl source")
        raw = load_from_jsonl(path)
        if max_rows is not None:
            raw = raw[:max_rows]
    elif source == "csv":
        if not path:
            raise ValueError("path required for csv source")
        raw = load_from_csv(path)
        if max_rows is not None:
            raw = raw[:max_rows]
    else:
        raise ValueError(f"Unknown source: {source}")

    preprocessed, pre_stats = preprocess_rows(raw)
    valid, val_errors = validate_records(preprocessed)

    report: dict[str, Any] = {
        "preprocess": pre_stats,
        "validation_errors_count": len(val_errors),
        "validation_sample_errors": val_errors[:10],
        "output_count": len(valid),
    }
    return valid, report


def records_to_jsonl(records: list[RestaurantRecord], out_path: str | Path) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")


def write_report(report: dict[str, Any], out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
