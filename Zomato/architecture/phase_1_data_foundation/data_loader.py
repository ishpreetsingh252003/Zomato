"""Load raw Zomato-style data from Hugging Face or a local JSON/JSONL/CSV path."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator

DEFAULT_HF_DATASET = "ManikaSaini/zomato-restaurant-recommendation"
DEFAULT_HF_SPLIT = "train"


def load_from_huggingface(
    dataset_id: str = DEFAULT_HF_DATASET,
    split: str = DEFAULT_HF_SPLIT,
    *,
    streaming: bool = False,
    max_rows: int | None = None,
) -> list[dict[str, Any]]:
    """
    Load the dataset into memory as a list of row dicts.
    For very large runs, use streaming=True and consume via iterate_huggingface_rows.
    """
    from datasets import load_dataset

    ds = load_dataset(dataset_id, split=split, streaming=streaming)
    if streaming:
        raise ValueError("Use iterate_huggingface_rows(..., streaming=True) for streaming.")

    rows: list[dict[str, Any]] = []
    n = len(ds) if max_rows is None else min(len(ds), max_rows)
    for i in range(n):
        rows.append(dict(ds[i]))
    return rows


def iterate_huggingface_rows(
    dataset_id: str = DEFAULT_HF_DATASET,
    split: str = DEFAULT_HF_SPLIT,
    *,
    streaming: bool = True,
) -> Iterator[dict[str, Any]]:
    """Yield one row at a time (memory-friendly)."""
    from datasets import load_dataset

    ds = load_dataset(dataset_id, split=split, streaming=streaming)
    for row in ds:
        yield dict(row)


def load_from_json(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, list):
        return [dict(x) for x in data]
    if isinstance(data, dict):
        return [dict(data)]
    raise ValueError(f"JSON root must be list or object, got {type(data)}")


def load_from_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_from_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]
