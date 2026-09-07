import json
from datetime import datetime, timezone
from typing import Any

from db.database import get_connection


# ── Sessions ──────────────────────────────────────────────────────────────────

def insert_session(session_id: str, job_role: str, skills: list[str], resume_text: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (id, created_at, job_role, skills, resume_text) VALUES (?,?,?,?,?)",
            (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                job_role,
                json.dumps(skills),
                resume_text,
            ),
        )


def get_session(session_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["skills"] = json.loads(d["skills"])
    return d


def update_session_role(session_id: str, job_role: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE sessions SET job_role = ? WHERE id = ?", (job_role, session_id))


# ── Turns ─────────────────────────────────────────────────────────────────────

def insert_turn(session_id: str, turn_num: int, question: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO turns (session_id, turn_num, question) VALUES (?,?,?)",
            (session_id, turn_num, question),
        )
        return cur.lastrowid  # type: ignore[return-value]


def update_turn_answer(
    turn_id: int,
    answer: str,
    score: int,
    strengths: str,
    weaknesses: str,
    feedback: str,
    follow_up: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE turns
               SET answer=?, score=?, strengths=?, weaknesses=?, feedback=?, follow_up=?
               WHERE id=?""",
            (answer, score, strengths, weaknesses, feedback, follow_up, turn_id),
        )


def get_turns(session_id: str, answered_only: bool = False) -> list[dict[str, Any]]:
    if answered_only:
        sql = "SELECT * FROM turns WHERE session_id = ? AND answer IS NOT NULL ORDER BY turn_num"
    else:
        sql = "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_num"
    with get_connection() as conn:
        rows = conn.execute(sql, (session_id,)).fetchall()
    return [dict(r) for r in rows]


def get_previous_questions(session_id: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT question FROM turns WHERE session_id = ? ORDER BY turn_num", (session_id,)
        ).fetchall()
    return [r["question"] for r in rows]


def next_turn_num(session_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(turn_num), 0) as mx FROM turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return row["mx"] + 1
