import sqlite3
import os
from pathlib import Path

from config import DB_PATH

_SCHEMA = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    sql = _SCHEMA.read_text()
    with get_connection() as conn:
        conn.executescript(sql)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)")}
        migrations = {
            "job_description": "ALTER TABLE sessions ADD COLUMN job_description TEXT NOT NULL DEFAULT ''",
            "skill_gap_summary": "ALTER TABLE sessions ADD COLUMN skill_gap_summary TEXT NOT NULL DEFAULT ''",
            "targeted_questions": "ALTER TABLE sessions ADD COLUMN targeted_questions TEXT NOT NULL DEFAULT '[]'",
        }
        for column, statement in migrations.items():
            if column not in columns:
                conn.execute(statement)
        if "current_difficulty" not in columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN current_difficulty TEXT NOT NULL DEFAULT 'medium'")
        turn_columns = {row["name"] for row in conn.execute("PRAGMA table_info(turns)")}
        if "ideal_model_answer" not in turn_columns:
            conn.execute("ALTER TABLE turns ADD COLUMN ideal_model_answer TEXT")
