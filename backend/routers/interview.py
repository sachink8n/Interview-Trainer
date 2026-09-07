from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import agent
import db.crud as crud

router = APIRouter(prefix="/interview", tags=["interview"])


class QuestionRequest(BaseModel):
    session_id: str


class QuestionResponse(BaseModel):
    turn_id: int
    turn_num: int
    question: str


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


class HistoryResponse(BaseModel):
    session_id: str
    turns: list[dict]


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
    )


@router.get("/history/{session_id}", response_model=HistoryResponse)
def get_history(session_id: str):
    session = crud.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    turns = crud.get_turns(session_id, answered_only=True)
    return HistoryResponse(session_id=session_id, turns=turns)
