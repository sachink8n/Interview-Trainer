import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

from config import UPLOAD_DIR
from services.resume_parser import extract_text, extract_skills

router = APIRouter(prefix="/resume", tags=["resume"])


class ResumeUploadResponse(BaseModel):
    session_id: str
    skills: list[str]
    resume_text_preview: str


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    session_id = str(uuid.uuid4())
    save_path = Path(UPLOAD_DIR) / f"{session_id}.pdf"

    content = await file.read()
    save_path.write_bytes(content)

    try:
        text = extract_text(save_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="PDF appears to be empty or image-only.")

    skills = extract_skills(text)

    return ResumeUploadResponse(
        session_id=session_id,
        skills=skills,
        resume_text_preview=text[:500],
    )
