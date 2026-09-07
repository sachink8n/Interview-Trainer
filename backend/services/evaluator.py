"""
Parses Granite's JSON evaluation response into a structured result.

Strengths and weaknesses are now returned as newline-separated bullet strings
so the frontend can render them as clean lists without ever showing raw
Python/JSON list syntax like ['item1', 'item2'].
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    score: int
    strengths: str      # newline-separated bullet points, e.g. "• Good clarity\n• Correct approach"
    weaknesses: str     # same format; empty string if none
    feedback: str
    follow_up_question: str


def _to_bullets(value: object) -> str:
    """
    Convert whatever Granite returns for strengths/weaknesses into a clean
    newline-separated bullet string.

    Handles:
      - list of strings  → "• item1\n• item2"
      - plain string     → kept as-is (or split on ". " / ", " heuristic)
      - stringified list → parsed, then bullets
    """
    if isinstance(value, list):
        items = [str(i).strip(" •-") for i in value if str(i).strip()]
        return "\n".join(f"• {i}" for i in items) if items else ""

    text = str(value).strip()
    if not text or text.lower() in ("none", "n/a", ""):
        return ""

    # Detect stringified Python list  ['item1', 'item2']
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text.replace("'", '"'))
            if isinstance(parsed, list):
                items = [str(i).strip(" •-") for i in parsed if str(i).strip()]
                return "\n".join(f"• {i}" for i in items)
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: strip brackets and split on commas
        inner = text[1:-1]
        items = [i.strip(" '\"") for i in inner.split(",") if i.strip(" '\"")]
        return "\n".join(f"• {i}" for i in items if i)

    # Plain string: if it already has bullets, leave it
    if text.startswith("•") or text.startswith("-"):
        return text

    # Split multi-sentence string on ". " boundary to make bullets
    sentences = re.split(r"\.\s+", text)
    if len(sentences) > 1:
        return "\n".join(f"• {s.rstrip('.')}." for s in sentences if s.strip())

    return f"• {text}"


def parse_evaluation(raw: str) -> EvaluationResult:
    """
    Extract JSON from Granite's response text and return an EvaluationResult.
    Falls back to safe defaults if parsing fails.
    """
    # Strip markdown fences Granite sometimes adds
    clean = re.sub(r"```(?:json)?", "", raw).strip()

    # Try to find the first {...} block
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            strengths = _to_bullets(data.get("strengths", []))
            weaknesses = _to_bullets(data.get("weaknesses", []))
            return EvaluationResult(
                score=max(1, min(10, int(data.get("score", 5)))),
                strengths=strengths,
                weaknesses=weaknesses,
                feedback=str(data.get("feedback", "")).strip(),
                follow_up_question=str(data.get("follow_up_question", "")).strip(),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # Graceful fallback — return the raw text as feedback
    return EvaluationResult(
        score=5,
        strengths="• Unable to parse structured feedback.",
        weaknesses="",
        feedback=raw[:600].strip() if raw else "No feedback available.",
        follow_up_question="Can you elaborate further on your answer?",
    )
