"""Resume-to-job-description analysis powered by IBM Granite."""
from __future__ import annotations

import json
import re

from services.granite import generate


def analyze(resume_text: str, job_description: str) -> tuple[str, list[str]]:
    """Return a concise skill-gap summary and exactly three interview questions."""
    prompt = f"""Compare this candidate resume with the job description.

RESUME:
{resume_text[:12000]}

JOB DESCRIPTION:
{job_description[:12000]}

Return ONLY valid JSON, with no markdown or extra text, in this exact shape:
{{
  "skill_gap_summary": "A concise summary of the strongest matches and most important missing or weakly evidenced skills.",
  "targeted_questions": ["Question 1?", "Question 2?", "Question 3?"]
}}

Make the three questions specific to gaps between the resume and job description. Each must be answerable in an interview and end with a question mark."""
    raw = generate(prompt)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise RuntimeError("Granite returned invalid skill-gap JSON")
    try:
        result = json.loads(match.group())
        summary = str(result["skill_gap_summary"]).strip()
        questions = [str(item).strip() for item in result["targeted_questions"] if str(item).strip()]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("Granite returned invalid skill-gap JSON") from exc
    if not summary or len(questions) != 3:
        raise RuntimeError("Granite must return a summary and exactly three questions")
    return summary, questions