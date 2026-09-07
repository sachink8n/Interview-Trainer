"""
Interview Trainer Agent — FastAPI backend entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from services.rag import build_index
from routers import resume, session, interview


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    build_index()
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="Interview Trainer Agent",
    description="AICTE Problem Statement #22 — AI-powered mock interview backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Frontend dev server; tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router)
app.include_router(session.router)
app.include_router(interview.router)


@app.get("/health")
def health():
    return {"status": "ok"}
