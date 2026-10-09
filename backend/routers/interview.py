import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import agent
import db.crud as crud
from services.speech_to_text import transcribe
from services.focus_tracker import tracker
from config import FOCUS_MAX_FRAME_BYTES

router = APIRouter(prefix="/interview", tags=["interview"])


class QuestionRequest(BaseModel):
    session_id: str


class QuestionResponse(BaseModel):
    turn_id: int
    turn_num: int
    question: str
    updated_difficulty: str


class AnswerRequest(BaseModel):
    session_id: str
    turn_id: int
    answer: str


class AnswerResponse(BaseModel):
    turn_id: int
    score: int
    strengths: str
    weaknesses: str
    feedback: str
    follow_up_question: str
    ideal_model_answer: str


class HistoryResponse(BaseModel):
    session_id: str
    turns: list[dict]


class TranscriptionResponse(BaseModel):
    transcript: str


class FocusFrameResponse(BaseModel):
    focus_score: float
    face_present: bool
    yaw: float | None
    pitch: float | None


@router.post("/focus/frame", response_model=FocusFrameResponse)
async def process_focus_frame(session_id: str = Form(...), frame: UploadFile = File(...)):
    """Process one ephemeral webcam frame without blocking the event loop."""
    frame_bytes = await frame.read()
    if not frame_bytes or len(frame_bytes) > FOCUS_MAX_FRAME_BYTES:
        raise HTTPException(status_code=400, detail="Frame is empty or too large.")
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Frame must be an image.")
    if crud.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    try:
        result = await asyncio.to_thread(tracker.process_frame, session_id, frame_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return FocusFrameResponse(
        focus_score=result.focus_score,
        face_present=result.face_present,
        yaw=result.yaw,
        pitch=result.pitch,
    )


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe a browser MediaRecorder upload with IBM Watson STT."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio recording is empty.")
    try:
        transcript = transcribe(audio_bytes, audio.content_type or "audio/webm")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Speech transcription failed: {exc}")
    return TranscriptionResponse(transcript=transcript)


@router.post("/question", response_model=QuestionResponse)
def get_question(body: QuestionRequest):
    try:
        result = agent.generate_question(body.session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {exc}")

    return QuestionResponse(
        turn_id=result.turn_id,
        turn_num=result.turn_num,
        question=result.question,
        updated_difficulty=result.updated_difficulty,
    )


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(body: AnswerRequest):
    if not body.answer or not body.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")

    try:
        result = agent.evaluate_answer(body.session_id, body.turn_id, body.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")

    return AnswerResponse(
        turn_id=result.turn_id,
        score=result.score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        feedback=result.feedback,
        follow_up_question=result.follow_up_question,
        ideal_model_answer=result.ideal_model_answer,
    )


@router.get("/history/{session_id}", response_model=HistoryResponse)
def get_history(session_id: str):
    session = crud.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    turns = crud.get_turns(session_id, answered_only=True)
    return HistoryResponse(session_id=session_id, turns=turns)
