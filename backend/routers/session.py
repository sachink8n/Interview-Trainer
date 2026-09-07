from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import db.crud as crud
from config import UPLOAD_DIR
from services.resume_parser import extract_text, extract_skills

router = APIRouter(prefix="/session", tags=["session"])


class SessionStartRequest(BaseModel):
    session_id: str
    job_role: str


class SessionStartResponse(BaseModel):
    session_id: str
    job_role: str
    skills: list[str]


class SessionDetailResponse(BaseModel):
    session_id: str
    job_role: str
    skills: list[str]
    created_at: str
    turns: list[dict]


@router.post("/start", response_model=SessionStartResponse)
def start_session(body: SessionStartRequest):
    """
    Attach a job_role to a session that was created by /resume/upload,
    then persist it in the database.
    """
    pdf_path = Path(UPLOAD_DIR) / f"{body.session_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Resume not found. Upload a PDF first.")

    # Check if session already exists (idempotent)
    existing = crud.get_session(body.session_id)
    if existing:
        crud.update_session_role(body.session_id, body.job_role)
        return SessionStartResponse(
            session_id=body.session_id,
            job_role=body.job_role,
            skills=existing["skills"],
        )

    text = extract_text(pdf_path)
    skills = extract_skills(text)

    crud.insert_session(
        session_id=body.session_id,
        job_role=body.job_role,
        skills=skills,
        resume_text=text,
    )

    return SessionStartResponse(
        session_id=body.session_id,
        job_role=body.job_role,
        skills=skills,
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str):
    session = crud.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    turns = crud.get_turns(session_id)
    return SessionDetailResponse(
        session_id=session["id"],
        job_role=session["job_role"],
        skills=session["skills"],
        created_at=session["created_at"],
        turns=turns,
    )
