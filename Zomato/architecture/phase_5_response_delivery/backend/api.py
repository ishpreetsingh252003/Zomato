"""REST API blueprint for Phase 5."""

from __future__ import annotations

import json
import traceback
from pathlib import Path

from flask import Blueprint, jsonify, request

from backend.orchestrator import run_pipeline, _load_sample_recommendations

api_bp = Blueprint("api", __name__, url_prefix="/api")

_PHASE5_DIR = Path(__file__).resolve().parents[1]


@api_bp.get("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "phase": 5, "service": "Zomato Recommendation API"})


@api_bp.get("/sample")
def sample():
    """Return pre-built sample recommendations for frontend demo."""
    data = _load_sample_recommendations()
    data["source"] = "sample"
    return jsonify(data)


@api_bp.post("/recommend")
def recommend():
    """
    Run the full recommendation pipeline.

    Expects JSON body:
    {
        "location": "Bangalore",
        "budget": "medium",
        "cuisines": ["Italian", "Chinese"],
        "min_rating": 4.0,
        "optional_preferences": ["quick-service"],
        "top_n": 5
    }
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate required fields
    location = (body.get("location") or "").strip()
    if not location:
        return jsonify({"error": "'location' is required"}), 400

    budget = (body.get("budget") or "medium").strip().lower()
    if budget not in {"low", "medium", "high"}:
        return jsonify({"error": "'budget' must be one of: low, medium, high"}), 400

    preferences = {
        "location": location,
        "budget": budget,
        "cuisines": body.get("cuisines") or [],
        "min_rating": float(body.get("min_rating") or 0.0),
        "optional_preferences": body.get("optional_preferences") or [],
    }
    top_n = int(body.get("top_n") or 5)
    top_n = max(1, min(top_n, 20))

    try:
        result = run_pipeline(preferences, top_n=top_n)
        return jsonify(result)
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500
