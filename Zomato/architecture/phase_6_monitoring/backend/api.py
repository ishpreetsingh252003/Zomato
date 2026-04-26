"""REST API blueprint for Phase 5."""

from __future__ import annotations

import json
import traceback
import time
from pathlib import Path

from flask import Blueprint, jsonify, request

from backend.orchestrator import run_pipeline, _load_sample_recommendations, get_metadata
import backend.analytics_logger as analytics_logger

api_bp = Blueprint("api", __name__, url_prefix="/api")

_PHASE6_DIR = Path(__file__).resolve().parents[1]


@api_bp.get("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "phase": 6, "service": "Zomato Recommendation API Phase 6"})


@api_bp.get("/sample")
def sample():
    """Return pre-built sample recommendations for frontend demo."""
    data = _load_sample_recommendations()
    data["source"] = "sample"
    return jsonify(data)


@api_bp.get("/metadata")
def metadata():
    """Return unique locations and cuisines for frontend dropdowns."""
    try:
        return jsonify(get_metadata())
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


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
        start_time = time.time()
        result = run_pipeline(preferences, top_n=top_n)
        latency_ms = (time.time() - start_time) * 1000.0
        
        # Log the query using Phase 6 analytics
        num_recs = len(result.get("recommendations", []))
        query_id = analytics_logger.log_query(preferences, num_recs, latency_ms)
        
        # Inject query_id into the result so frontend can use it for feedback
        result["query_id"] = query_id
        
        return jsonify(result)
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500

@api_bp.post("/analytics/feedback")
def submit_feedback():
    """Accepts explicit user feedback on recommendations."""
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400
        
    query_id = body.get("query_id")
    restaurant_name = body.get("restaurant_name")
    feedback_type = body.get("feedback_type")
    
    if not query_id or not restaurant_name or not feedback_type:
        return jsonify({"error": "query_id, restaurant_name, and feedback_type are required"}), 400
        
    if feedback_type not in ["like", "dislike"]:
        return jsonify({"error": "feedback_type must be 'like' or 'dislike'"}), 400
        
    try:
        analytics_logger.log_feedback(query_id, restaurant_name, feedback_type)
        return jsonify({"status": "success", "message": "Feedback recorded."})
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500
