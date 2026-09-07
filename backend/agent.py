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


@dataclass
class AnswerResult:
    turn_id: int
    score: int
    strengths: str
    weaknesses: str
    feedback: str
    follow_up_question: str


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

    # Build a rich RAG query from job role + skills + resume snippet
    rag_query = f"{job_role} interview questions {' '.join(skills[:5])} {resume_text[:300]}"
    rag_chunks = rag.retrieve(rag_query, top_k=3)

    previous_questions = crud.get_previous_questions(session_id)
    turn_num = crud.next_turn_num(session_id)

    prompt = prompt_builder.build_question_prompt(
        job_role=job_role,
        skills=skills,
        rag_chunks=rag_chunks,
        previous_questions=previous_questions,
        turn_num=turn_num,
    )

    raw_question = granite.generate(prompt)

    # Clean up: extract first sentence/question ending with '?'
    question = _clean_question(raw_question)

    turn_id = crud.insert_turn(session_id, turn_num, question)
    return QuestionResult(turn_id=turn_id, turn_num=turn_num, question=question)


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

    prompt = prompt_builder.build_evaluation_prompt(
        job_role=job_role,
        skills=skills,
        question=question,
        answer=answer,
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
    )

    return AnswerResult(
        turn_id=turn_id,
        score=result.score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        feedback=result.feedback,
        follow_up_question=result.follow_up_question,
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
