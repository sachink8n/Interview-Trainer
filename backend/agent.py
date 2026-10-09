"""
Interview Agent — single orchestrator that:
  1. Retrieves relevant context via RAG
  2. Builds a personalised question prompt
  3. Calls Granite to generate the question
  4. Persists the turn in SQLite
  5. Accepts the candidate's answer
  6. Builds an evaluation prompt
  7. Calls Granite to evaluate
  8. Persists the evaluation
  9. Returns structured feedback + follow-up
"""
from __future__ import annotations

from dataclasses import dataclass

import db.crud as crud
from services import rag, granite, prompt_builder, evaluator


@dataclass
class QuestionResult:
    turn_id: int
    turn_num: int
    question: str
    updated_difficulty: str


@dataclass
class AnswerResult:
    turn_id: int
    score: int
    strengths: str
    weaknesses: str
    feedback: str
    follow_up_question: str
    ideal_model_answer: str


def generate_question(session_id: str) -> QuestionResult:
    """
    RAG + Granite → new interview question.
    Persists the turn (without answer) and returns QuestionResult.
    """
    session = crud.get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id!r} not found")

    job_role: str = session["job_role"]
    skills: list[str] = session["skills"]
    resume_text: str = session["resume_text"]
    job_description: str = session.get("job_description", "")

    rag_query = f"{job_role} interview gaps {' '.join(skills[:5])} {job_description[:500]}"
    rag_chunks = rag.retrieve(
        rag_query,
        top_k=5,
        extra_texts=[(resume_text, "resume"), (job_description, "job description")]
        if job_description
        else None,
    )

    previous_questions = crud.get_previous_questions(session_id)
    turn_num = crud.next_turn_num(session_id)
    previous_turns = crud.get_turns(session_id, answered_only=True)
    previous_turn = previous_turns[-1] if previous_turns else None
    current_difficulty = str(session.get("current_difficulty", "medium")).lower()
    if current_difficulty not in {"easy", "medium", "hard"}:
        current_difficulty = "medium"

    prompt = prompt_builder.build_adaptive_question_prompt(
        current_difficulty=current_difficulty,
        previous_question=previous_turn["question"] if previous_turn else "",
        user_answer=previous_turn["answer"] if previous_turn else "",
        previous_score=previous_turn["score"] if previous_turn else None,
        role_context=f"{job_role}; skills: {', '.join(skills)}; category: {prompt_builder.get_question_category(turn_num)}; reference: {' '.join(rag_chunks[:2])}",
    )

    raw_question = granite.generate(prompt)
    question, proposed_difficulty = _parse_adaptive_question(raw_question, current_difficulty)
    updated_difficulty = _enforce_difficulty(
        current_difficulty,
        previous_turn["score"] if previous_turn else None,
        proposed_difficulty,
    )
    crud.update_session_difficulty(session_id, updated_difficulty)

    turn_id = crud.insert_turn(session_id, turn_num, question)
    return QuestionResult(turn_id=turn_id, turn_num=turn_num, question=question, updated_difficulty=updated_difficulty)


def evaluate_answer(session_id: str, turn_id: int, answer: str) -> AnswerResult:
    """
    Granite → evaluate candidate answer.
    Persists the evaluation and returns AnswerResult.
    """
    session = crud.get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id!r} not found")

    # Fetch the question from the turn
    turns = crud.get_turns(session_id)
    turn = next((t for t in turns if t["id"] == turn_id), None)
    if turn is None:
        raise ValueError(f"Turn {turn_id} not found in session {session_id!r}")

    question = turn["question"]
    job_role: str = session["job_role"]
    skills: list[str] = session["skills"]
    category = prompt_builder.get_question_category(turn["turn_num"])

    prompt = prompt_builder.build_evaluation_prompt(
        job_role=job_role,
        skills=skills,
        question=question,
        answer=answer,
        category=category,
    )

    raw_eval = granite.generate(prompt)
    result = evaluator.parse_evaluation(raw_eval)

    crud.update_turn_answer(
        turn_id=turn_id,
        answer=answer,
        score=result.score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        feedback=result.feedback,
        follow_up=result.follow_up_question,
        ideal_model_answer=result.ideal_model_answer,
    )

    return AnswerResult(
        turn_id=turn_id,
        score=result.score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        feedback=result.feedback,
        follow_up_question=result.follow_up_question,
        ideal_model_answer=result.ideal_model_answer,
    )


def _clean_question(raw: str) -> str:
    """Extract the first meaningful question from Granite's output."""
    import re

    # Remove common prefixes granite sometimes adds
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    for line in lines:
        # Skip lines that are clearly meta-commentary
        if line.lower().startswith(("question:", "here is", "here's", "sure", "of course")):
            continue
        if "?" in line:
            # Take up to the first '?' and restore it
            q = line.split("?")[0].strip() + "?"
            return q

    # Fallback: return first non-empty line
    return lines[0] if lines else raw.strip()


def _parse_adaptive_question(raw: str, fallback_difficulty: str) -> tuple[str, str]:
    """Parse Granite's adaptive JSON and safely fall back to its prior level."""
    import json
    import re

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            question = str(data["question"]).strip()
            difficulty = str(data["updated_difficulty"]).lower().strip()
            if question and difficulty in {"easy", "medium", "hard"}:
                return _clean_question(question), difficulty
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            pass
    return _clean_question(raw), fallback_difficulty


def _enforce_difficulty(current: str, previous_score: int | None, proposed: str) -> str:
    """Keep Granite's level within the score-driven progression rules."""
    levels = ("easy", "medium", "hard")
    current_index = levels.index(current)
    if previous_score is None or 5 <= previous_score <= 7:
        return current
    if previous_score >= 8:
        return levels[min(current_index + 1, len(levels) - 1)]
    return levels[max(current_index - 1, 0)]
