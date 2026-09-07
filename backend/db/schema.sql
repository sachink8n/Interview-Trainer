CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    job_role    TEXT NOT NULL,
    skills      TEXT NOT NULL,   -- JSON array
    resume_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id),
    turn_num    INTEGER NOT NULL,
    question    TEXT NOT NULL,
    answer      TEXT,
    score       INTEGER,
    strengths   TEXT,
    weaknesses  TEXT,
    feedback    TEXT,
    follow_up   TEXT
);
