"""CLI for Phase 3 candidate retrieval and filtering."""

from __future__ import annotations

import argparse
import json

from pipeline import load_restaurants_from_jsonl, run_phase3


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3: Candidate Retrieval and Filtering")
    parser.add_argument("--web", action="store_true", help="Start basic web UI")
    parser.add_argument("--dataset-path", default="", help="Path to cleaned restaurant JSONL")
    parser.add_argument("--location", default="")
    parser.add_argument("--budget", default="medium")
    parser.add_argument("--cuisines", default="")
    parser.add_argument("--min-rating", default="0")
    parser.add_argument("--optional-preferences", default="")
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    if args.web:
        from web_ui import main as web_main

        web_main()
        return

    if not args.dataset_path:
        raise ValueError("--dataset-path is required for CLI mode")

    restaurants = load_restaurants_from_jsonl(args.dataset_path)
    payload = {
        "location": args.location,
        "budget": args.budget,
        "cuisines": [x.strip() for x in args.cuisines.split(",") if x.strip()],
        "min_rating": args.min_rating,
        "optional_preferences": [
            x.strip().lower() for x in args.optional_preferences.split(",") if x.strip()
        ],
    }
    candidates, report = run_phase3(restaurants, payload, top_n=args.top_n)
    print("Top Candidates:")
    print(json.dumps([c.model_dump() for c in candidates], indent=2))
    print("\nReport:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
