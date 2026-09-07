"""
Builds prompts for question generation and answer evaluation.

Question rotation covers 8 categories across an 8-question interview:
  1  → resume/project-based warm-up
  2  → DSA / coding problem (write code or trace execution)
  3  → CS fundamentals (OS, networks, OOP, etc.)
  4  → backend / API design
  5  → database / SQL
  6  → system design
  7  → algorithm analysis (time/space complexity, trade-offs)
  8  → behavioral / HR (STAR method)

For non-8 interviews the category is chosen by (turn_num - 1) % 8 so the
rotation always covers all categories without repetition.
"""
from __future__ import annotations

import random
from config import MAX_PREVIOUS_QUESTIONS

# ── Question-type catalogue ───────────────────────────────────────────────────

# Each entry: (category_label, detailed_instruction)
_QUESTION_TYPES = [
    # 0 — resume / project warm-up
    (
        "resume/project",
        (
            "Ask a specific question about ONE of the candidate's listed skills or projects. "
            "Reference a concrete technology they know (e.g. if they know Python/FastAPI, ask about "
            "a design decision they would make). Make it a medium-difficulty warm-up."
        ),
    ),
    # 1 — DSA / coding
    (
        "DSA/coding",
        (
            "Ask a coding or DSA question that requires the candidate to WRITE CODE or describe "
            "an algorithm step-by-step. Choose ONE of the following sub-types at random:\n"
            "  a) Write a function: give a clear problem statement and ask them to implement it.\n"
            "  b) Trace/predict output: show a short code snippet and ask what it returns.\n"
            "  c) Debug: show broken code and ask them to find and fix the bug.\n"
            "  d) Improve: show an O(n²) or naive solution and ask for a better one.\n"
            "Pick a topic relevant to the job role (arrays, trees, graphs, strings, DP, etc.). "
            "Difficulty: medium (B.Tech/entry–mid-level interview)."
        ),
    ),
    # 2 — CS fundamentals
    (
        "CS fundamentals",
        (
            "Ask a conceptual question about computer science fundamentals relevant to the role. "
            "Topics to pick from (choose the most relevant): process vs thread, memory management, "
            "TCP/IP vs UDP, HTTP vs HTTPS, caching strategies, OOP principles (SOLID), "
            "virtual memory, garbage collection, or concurrency primitives. "
            "Ask for a concrete explanation or comparison, not just a definition."
        ),
    ),
    # 3 — backend / API
    (
        "backend/API",
        (
            "Ask a backend engineering or API design question. Pick ONE sub-type:\n"
            "  a) REST API design: ask them to design endpoints for a given feature.\n"
            "  b) Authentication: ask how they would implement JWT or OAuth.\n"
            "  c) Error handling: how should a production API handle failures?\n"
            "  d) Rate limiting / pagination: ask for an approach.\n"
            "Make the question concrete and scenario-based."
        ),
    ),
    # 4 — database / SQL
    (
        "database/SQL",
        (
            "Ask a database or SQL question. Choose ONE sub-type:\n"
            "  a) Write a SQL query for a described scenario (JOIN, GROUP BY, subquery, window fn).\n"
            "  b) Schema design: design tables for a small feature.\n"
            "  c) Indexing strategy: when and why would you add an index?\n"
            "  d) SQL vs NoSQL trade-off for a given use case.\n"
            "Keep it at medium difficulty — not a trivial SELECT."
        ),
    ),
    # 5 — system design
    (
        "system design",
        (
            "Ask a system design question appropriate for a B.Tech / junior–mid level engineer. "
            "Choose a moderately scoped system (not 'design Twitter from scratch'). Examples: "
            "URL shortener, notification service, rate limiter, file upload service, "
            "simple leaderboard, or basic recommendation feed. "
            "Ask the candidate to describe the high-level components and one key design decision."
        ),
    ),
    # 6 — algorithm analysis
    (
        "algorithm analysis",
        (
            "Ask a question that requires the candidate to ANALYZE time/space complexity or "
            "COMPARE two algorithmic approaches. Sub-types:\n"
            "  a) Give two solutions to the same problem and ask which is better and why.\n"
            "  b) Ask for the time and space complexity of a given algorithm or data structure operation.\n"
            "  c) Ask when to use one data structure vs another for a specific access pattern.\n"
            "Do NOT simply ask 'what is Big-O of binary search' — make it applied."
        ),
    ),
    # 7 — behavioral / HR
    (
        "behavioral/HR",
        (
            "Ask a behavioral or situational question using the STAR method framework. "
            "Choose ONE topic: leadership, handling failure, conflict resolution, "
            "time management under pressure, working with ambiguous requirements, "
            "receiving critical feedback, or a 'tell me about a project you are proud of' style. "
            "Frame it as a real scenario question, not a generic 'tell me about yourself'."
        ),
    ),
]


def _pick_question_type(turn_num: int) -> tuple[str, str]:
    """Return (category_label, instruction) for the given turn number."""
    idx = (turn_num - 1) % len(_QUESTION_TYPES)
    return _QUESTION_TYPES[idx]


def build_question_prompt(
    job_role: str,
    skills: list[str],
    rag_chunks: list[str],
    previous_questions: list[str],
    turn_num: int,
) -> str:
    skills_str = ", ".join(skills) if skills else "general software engineering"
    context_str = "\n\n".join(rag_chunks) if rag_chunks else ""

    recent = previous_questions[-MAX_PREVIOUS_QUESTIONS:]
    prev_str = (
        "\n".join(f"- {q}" for q in recent) if recent else "None yet."
    )

    category, instruction = _pick_question_type(turn_num)

    context_block = (
        f"\nReference Knowledge (use only if relevant):\n{context_str}\n"
        if context_str
        else ""
    )

    prompt = f"""You are a senior technical interviewer conducting a real {job_role} interview.

Candidate's Skills: {skills_str}
{context_block}
Previously Asked Questions (do NOT repeat or closely paraphrase any of these):
{prev_str}

--- CURRENT QUESTION INSTRUCTIONS ---
Category: {category}
{instruction}

Rules:
- The question MUST be specific to the {job_role} role and the candidate's actual skills where possible.
- Output exactly ONE question — no greetings, no preamble, no multiple-choice options.
- For coding questions, include a short concrete problem statement (e.g. function signature or input/output example).
- End the question with a question mark.
- Do not reveal the answer or hint at the expected answer.

Question:"""

    return prompt


def build_evaluation_prompt(
    job_role: str,
    skills: list[str],
    question: str,
    answer: str,
) -> str:
    skills_str = ", ".join(skills) if skills else "general skills"

    prompt = f"""You are a strict but fair technical interviewer evaluating a candidate's answer for a {job_role} role.

Candidate Skills: {skills_str}

Question: {question}

Candidate's Answer: {answer}

Evaluate the answer across these five dimensions:
1. Correctness — Is the answer technically accurate?
2. Relevance — Does it address the question asked?
3. Technical Depth — Does it show understanding beyond surface level?
4. Clarity — Is the explanation clear and well-structured?
5. Completeness — Does it cover all key aspects?

Respond ONLY with valid JSON in exactly this format (no markdown, no extra text):
{{
  "score": <integer 1-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness or gap 1>", "<weakness or gap 2>"],
  "feedback": "<2-3 sentences of specific, constructive feedback referencing the question>",
  "follow_up_question": "<one focused follow-up question that either digs deeper into a gap or advances the topic>"
}}

Scoring guide:
9-10: Excellent — comprehensive, accurate, well-structured, handles edge cases or complexity
7-8: Good — mostly correct with minor gaps or imprecision
5-6: Average — surface-level correctness, missing depth or key points
3-4: Below average — partially correct, significant conceptual gaps
1-2: Poor — incorrect, irrelevant, or very incomplete

If there are no weaknesses (score >= 9), set "weaknesses" to [].
Both "strengths" and "weaknesses" must be plain string arrays — no nested objects.

JSON:"""

    return prompt
