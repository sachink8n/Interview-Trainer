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
from services.interview_state import InterviewSessionState

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
    """Return the deterministic phase/category for the requested turn."""
    if turn_num <= 2:
        return (
            "Phase 1 - Introduction",
            "Ask about the candidate's background, resume, motivation, or experience. Keep it open-ended and welcoming.",
        )
    if turn_num <= 6:
        return (
            "Phase 2 - Technical",
            "Ask one role-specific technical question involving problem solving, fundamentals, implementation, or system design. Make it medium difficulty.",
        )
    return (
        "Phase 3 - HR/Behavioral",
        "Ask one behavioral question about leadership, conflict, failure, ambiguity, feedback, or teamwork. Invite a concrete real experience so it can be answered using STAR.",
    )


def get_question_category(turn_num: int) -> str:
    """Return the category used to evaluate a generated question."""
    return InterviewSessionState(turn_num).category_label


def build_question_prompt(
    job_role: str,
    skills: list[str],
    rag_chunks: list[str],
    previous_questions: list[str],
    turn_num: int,
    job_description: str = "",
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
Job Description:
{job_description[:6000] if job_description else "Not provided."}
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
    category: str = "",
) -> str:
    skills_str = ", ".join(skills) if skills else "general skills"

    is_hr = category.startswith("Phase 3")
    star_instruction = """
For this HR/Behavioral answer, strictly evaluate the STAR method:
- Situation: Did the candidate clearly set the context?
- Task: Did they explain their responsibility or goal?
- Action: Did they describe specific actions they personally took?
- Result: Did they give a concrete outcome, impact, or learning?
The score must reflect missing STAR components. Mention exactly which components are missing in feedback.
""" if is_hr else ""
    model_answer_field = '  "ideal_model_answer": "<a concise ideal STAR answer covering Situation, Task, Action, and Result>"' if is_hr else '  "ideal_model_answer": ""'

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
{star_instruction}

Respond ONLY with valid JSON in exactly this format (no markdown, no extra text):
{{
  "score": <integer 1-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness or gap 1>", "<weakness or gap 2>"],
  "feedback": "<2-3 sentences of specific, constructive feedback referencing the question>",
    "follow_up_question": "<one focused follow-up question that either digs deeper into a gap or advances the topic>",
{model_answer_field}
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


def build_adaptive_question_prompt(
    current_difficulty: str,
    previous_question: str,
    user_answer: str,
    previous_score: int | None,
    role_context: str = "",
) -> str:
    """Build a JSON-only prompt for the next adaptive interview question."""
    score = "Not available (this is the first question)." if previous_score is None else str(previous_score)
    return f"""You are generating the next question in an interview for {role_context or 'a software engineering role'}.

Current difficulty: {current_difficulty.title()}
Previous question: {previous_question or "None - start the interview."}
User answer: {user_answer or "None - start the interview."}
Previous score: {score}

Difficulty rules:
- If previous_score is 8 or higher, increase the next question's difficulty by one level.
- If previous_score is 4 or lower, generate a foundational/easier question and decrease the level by one when possible.
- If previous_score is 5, 6, or 7, keep the current difficulty.
- Difficulty must remain one of Easy, Medium, or Hard.
- On the first question, keep the current difficulty and ask a clear introductory question.
- Do not repeat or closely paraphrase the previous question.

Return ONLY valid JSON with exactly this shape:
{{
  "question": "One focused interview question?",
  "updated_difficulty": "Easy|Medium|Hard"
}}"""
