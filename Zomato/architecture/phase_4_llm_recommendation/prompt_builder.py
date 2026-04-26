"""Prompt builder for Groq-based ranking and explanation generation."""

from __future__ import annotations

import json

from schema import CandidateInput, PreferencesInput


def build_prompt(preferences: PreferencesInput, candidates: list[CandidateInput], top_n: int) -> str:
    prefs_json = json.dumps(preferences.model_dump(), indent=2)
    cands_json = json.dumps([c.model_dump() for c in candidates], indent=2)
    return f"""
You are an assistant that ranks restaurant candidates for a user.

Task:
1) Rank the best {top_n} restaurants based on user preferences.
2) Give concise, specific reasoning for each choice.
3) Do not invent restaurants or fields not in the candidate list.

User Preferences:
{prefs_json}

Candidate Restaurants:
{cands_json}

Output requirements:
- Return ONLY valid JSON.
- No markdown, no extra text.
- Use this exact schema:
{{
  "summary": "short summary sentence",
  "recommendations": [
    {{
      "rank": 1,
      "restaurant_name": "string",
      "explanation": "string",
      "rating": 4.2,
      "cost_for_two": 1200,
      "cuisine": "Italian, Continental"
    }}
  ]
}}
""".strip()
