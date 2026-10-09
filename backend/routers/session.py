from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import db.crud as crud
from config import UPLOAD_DIR
from services.resume_parser import extract_text, extract_skills
from services.skill_gap import analyze

router = APIRouter(prefix="/session", tags=["session"])


class SessionStartRequest(BaseModel):
    session_id: str
    job_role: str
    job_description: str = ""


class SessionStartResponse(BaseModel):
    session_id: str
    job_role: str
    skills: list[str]
    skill_gap_summary: str = ""
    targeted_questions: list[str] = []


class SessionDetailResponse(BaseModel):
    session_id: str
    job_role: str
    skills: list[str]
    created_at: str
    turns: list[dict]
    job_description: str = ""
    skill_gap_summary: str = ""
    targeted_questions: list[str] = []


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
            skill_gap_summary=existing.get("skill_gap_summary", ""),
            targeted_questions=existing.get("targeted_questions", []),
        )

    text = extract_text(pdf_path)
    skills = extract_skills(text)
    summary = ""
    targeted_questions: list[str] = []
    if body.job_description.strip():
        try:
            summary, targeted_questions = analyze(text, body.job_description)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))

    crud.insert_session(
        session_id=body.session_id,
        job_role=body.job_role,
        skills=skills,
        resume_text=text,
        job_description=body.job_description.strip(),
        skill_gap_summary=summary,
        targeted_questions=targeted_questions,
    )

    return SessionStartResponse(
        session_id=body.session_id,
        job_role=body.job_role,
        skills=skills,
        skill_gap_summary=summary,
        targeted_questions=targeted_questions,
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
        job_description=session.get("job_description", ""),
        skill_gap_summary=session.get("skill_gap_summary", ""),
        targeted_questions=session.get("targeted_questions", []),
    )
