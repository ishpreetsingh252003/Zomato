"""Flask application factory for Phase 5."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

_PHASE5_DIR = Path(__file__).resolve().parents[1]
_FRONTEND_DIR = _PHASE5_DIR / "frontend"


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(_FRONTEND_DIR),
        static_url_path="",
    )
    CORS(app)

    # Register API blueprint
    from backend.api import api_bp  # noqa: PLC0415

    app.register_blueprint(api_bp)

    # Serve the SPA for any non-API route
    @app.get("/")
    def index():
        return send_from_directory(str(_FRONTEND_DIR), "index.html")

    @app.get("/css/<path:filename>")
    def css(filename: str):
        return send_from_directory(str(_FRONTEND_DIR / "css"), filename)

    @app.get("/js/<path:filename>")
    def js(filename: str):
        return send_from_directory(str(_FRONTEND_DIR / "js"), filename)

    return app
