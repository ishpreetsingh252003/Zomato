import sqlite3
import json
import uuid
import time
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parent.parent / "analytics.db"

def _get_connection():
    """Get a connection to the SQLite database."""
    return sqlite3.connect(str(_DB_PATH))

def initialize_db():
    """Create the required tables if they don't exist."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        query_id TEXT PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        location TEXT,
        budget TEXT,
        cuisines TEXT,
        min_rating REAL,
        optional_preferences TEXT,
        num_recommendations INTEGER,
        latency_ms REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        restaurant_name TEXT,
        feedback_type TEXT,
        FOREIGN KEY(query_id) REFERENCES queries(query_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def log_query(preferences: dict, num_recommendations: int, latency_ms: float) -> str:
    """Log a user query and return the generated query_id."""
    query_id = str(uuid.uuid4())
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO queries (
            query_id, location, budget, cuisines, min_rating, 
            optional_preferences, num_recommendations, latency_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        query_id,
        preferences.get("location", ""),
        preferences.get("budget", ""),
        json.dumps(preferences.get("cuisines", [])),
        preferences.get("min_rating", 0.0),
        json.dumps(preferences.get("optional_preferences", [])),
        num_recommendations,
        latency_ms
    ))
    
    conn.commit()
    conn.close()
    return query_id

def log_feedback(query_id: str, restaurant_name: str, feedback_type: str):
    """Log user feedback (like/dislike) for a specific restaurant recommendation."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO feedback (query_id, restaurant_name, feedback_type)
        VALUES (?, ?, ?)
    ''', (query_id, restaurant_name, feedback_type))
    
    conn.commit()
    conn.close()

# Ensure tables are created when the module is imported
initialize_db()
