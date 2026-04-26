"""CLI: run from this directory: python __main__.py [args]"""

from __future__ import annotations

import argparse

from pipeline import records_to_jsonl, run_phase1, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: Data Foundation pipeline")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start basic web UI (form → Hugging Face download → Phase 1)",
    )
    parser.add_argument(
        "--source",
        choices=("huggingface", "json", "jsonl", "csv"),
        default="huggingface",
    )
    parser.add_argument("--path", default=None, help="File path for json/jsonl/csv")
    parser.add_argument("--dataset-id", default="ManikaSaini/zomato-restaurant-recommendation")
    parser.add_argument("--split", default="train")
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--out-jsonl", default=None, help="Write validated records as JSONL")
    parser.add_argument("--report-json", default=None, help="Write run report JSON")
    args = parser.parse_args()

    if args.web:
        from web_ui import main as web_main

        web_main()
        return

    records, report = run_phase1(
        source=args.source,
        path=args.path,
        dataset_id=args.dataset_id,
        split=args.split,
        max_rows=args.max_rows,
    )
    print(f"Validated records: {len(records)}")
    print(f"Report: {report}")

    if args.out_jsonl:
        records_to_jsonl(records, args.out_jsonl)
    if args.report_json:
        write_report(report, args.report_json)


if __name__ == "__main__":
    main()
