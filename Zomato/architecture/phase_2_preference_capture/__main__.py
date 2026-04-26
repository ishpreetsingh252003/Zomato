"""CLI for Phase 2 preference capture layer."""

from __future__ import annotations

import argparse
import json

from pipeline import run_phase2


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2: Preference Capture Layer")
    parser.add_argument("--web", action="store_true", help="Start basic web UI")
    parser.add_argument("--location", default="")
    parser.add_argument("--budget", default="medium")
    parser.add_argument("--cuisines", default="")
    parser.add_argument("--min-rating", default="0")
    parser.add_argument("--optional-preferences", default="")
    parser.add_argument("--free-text", default="")
    args = parser.parse_args()

    if args.web:
        from web_ui import main as web_main

        web_main()
        return

    prefs, report = run_phase2(
        {
            "location": args.location,
            "budget": args.budget,
            "cuisines": args.cuisines,
            "min_rating": args.min_rating,
            "optional_preferences": args.optional_preferences,
            "free_text": args.free_text,
        }
    )
    print("Validated Preferences:")
    print(json.dumps(prefs.model_dump(), indent=2))
    print("\nReport:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
