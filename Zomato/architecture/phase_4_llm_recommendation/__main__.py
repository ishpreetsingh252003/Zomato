"""CLI entrypoint for Phase 4 Groq recommendation generation."""

from __future__ import annotations

import argparse
import json

from pipeline import load_candidates_json, load_preferences_json, run_phase4


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4: LLM Reasoning and Recommendation (Groq)")
    parser.add_argument("--web", action="store_true", help="Start basic web UI")
    parser.add_argument("--candidates-path", default="", help="Path to shortlisted candidates JSON")
    parser.add_argument("--preferences-path", default="", help="Path to preferences JSON")
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    args = parser.parse_args()

    if args.web:
        from web_ui import main as web_main

        web_main()
        return

    if not args.candidates_path or not args.preferences_path:
        raise ValueError("--candidates-path and --preferences-path are required in CLI mode")

    candidates = load_candidates_json(args.candidates_path)
    prefs = load_preferences_json(args.preferences_path)
    response, report = run_phase4(prefs, candidates, top_n=args.top_n, model=args.model)

    print("LLM Recommendations:")
    print(json.dumps(response.model_dump(), indent=2))
    print("\nReport:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
