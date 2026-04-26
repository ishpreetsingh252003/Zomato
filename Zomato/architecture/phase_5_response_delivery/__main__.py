"""CLI entrypoint for Phase 5: Response Delivery and UX."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from this directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Ensure this package is importable when run as `python __main__.py`
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 5: Response Delivery and UX — Flask backend + premium frontend"
    )
    parser.add_argument(
        "--port", type=int, default=5004, help="Port to run the server on (default: 5004)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run Flask in debug mode"
    )
    args = parser.parse_args()

    from backend.app import create_app

    app = create_app()
    print(f"\n  Phase 5 — Zomato Recommendation UI")
    print(f"  Running at: http://{args.host}:{args.port}/")
    print(f"  API health: http://{args.host}:{args.port}/api/health")
    print(f"  API sample: http://{args.host}:{args.port}/api/sample\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
