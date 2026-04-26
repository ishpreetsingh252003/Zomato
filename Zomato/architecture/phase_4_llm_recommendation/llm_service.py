"""Groq LLM service wrapper for Phase 4."""

from __future__ import annotations

import json
import os
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

from schema import LLMResponse


DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


def call_groq_json(prompt: str, model: str = DEFAULT_GROQ_MODEL, temperature: float = 0.2) -> LLMResponse:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY environment variable.")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You are a precise recommendation ranker that returns JSON only."},
            {"role": "user", "content": prompt},
        ],
    )

    content = completion.choices[0].message.content or ""
    cleaned = content.strip()
    # best effort to isolate JSON object if model adds wrapping text
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model response is not JSON: {cleaned[:400]}")
    parsed = json.loads(cleaned[start : end + 1])
    return LLMResponse.model_validate(parsed)
