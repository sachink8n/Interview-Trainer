// Typed API client for the Interview Trainer FastAPI backend.
// All backend calls go through this module.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

// ── Types ────────────────────────────────────────────────────────────────────

export interface ResumeUploadResponse {
  session_id: string;
  skills: string[];
  resume_text_preview: string;
}

export interface SessionStartResponse {
  session_id: string;
  job_role: string;
  skills: string[];
  skill_gap_summary: string;
  targeted_questions: string[];
}

export interface SessionDetail {
  session_id: string;
  job_role: string;
  skills: string[];
  created_at: string;
  turns: Turn[];
  job_description: string;
  skill_gap_summary: string;
  targeted_questions: string[];
}

export interface Turn {
  id: number;
  session_id: string;
  turn_num: number;
  question: string;
  answer: string | null;
  score: number | null;
  strengths: string | null;
  weaknesses: string | null;
  feedback: string | null;
  follow_up: string | null;
  ideal_model_answer: string | null;
}

export interface QuestionResponse {
  turn_id: number;
  turn_num: number;
  question: string;
  updated_difficulty: 'easy' | 'medium' | 'hard';
}

export interface AnswerResponse {
  turn_id: number;
  score: number;
  strengths: string;
  weaknesses: string;
  feedback: string;
  follow_up_question: string;
  ideal_model_answer: string;
}

export interface HistoryResponse {
  session_id: string;
  turns: Turn[];
}

export interface TranscriptionResponse {
  transcript: string;
}

export interface FocusFrameResponse {
  focus_score: number;
  face_present: boolean;
  yaw: number | null;
  pitch: number | null;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── API calls ─────────────────────────────────────────────────────────────────

/** Upload a resume PDF. Returns session_id + detected skills. */
export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE_URL}/resume/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Upload failed: ${res.status}`);
  }
  return res.json();
}

/** Attach a job_role to the session and persist to DB. */
export async function startSession(
  session_id: string,
  job_role: string,
  job_description: string,
): Promise<SessionStartResponse> {
  return request<SessionStartResponse>('/session/start', {
    method: 'POST',
    body: JSON.stringify({ session_id, job_role, job_description }),
  });
}

/** Fetch full session including all turns. */
export async function getSession(session_id: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/session/${session_id}`);
}

/** Ask the agent for the next interview question. */
export async function getQuestion(session_id: string): Promise<QuestionResponse> {
  return request<QuestionResponse>('/interview/question', {
    method: 'POST',
    body: JSON.stringify({ session_id }),
  });
}

/** Submit answer for a turn; returns evaluation. */
export async function submitAnswer(
  session_id: string,
  turn_id: number,
  answer: string,
): Promise<AnswerResponse> {
  return request<AnswerResponse>('/interview/answer', {
    method: 'POST',
    body: JSON.stringify({ session_id, turn_id, answer }),
  });
}

/** Send a MediaRecorder audio blob to IBM Watson Speech-to-Text. */
export async function transcribeAudio(audio: Blob): Promise<TranscriptionResponse> {
  const form = new FormData();
  form.append('audio', audio, 'answer.webm');
  const res = await fetch(`${BASE_URL}/interview/transcribe`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Transcription failed: ${res.status}`);
  }
  return res.json();
}

/** Send one ephemeral webcam frame for server-side focus estimation. */
export async function sendFocusFrame(session_id: string, frame: Blob): Promise<FocusFrameResponse> {
  const form = new FormData();
  form.append('session_id', session_id);
  form.append('frame', frame, 'focus.jpg');
  const res = await fetch(`${BASE_URL}/interview/focus/frame`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `Focus tracking failed: ${res.status}`);
  }
  return res.json();
}

/** Fetch all turns for a session (interview history). */
export async function getHistory(session_id: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/interview/history/${session_id}`);
}
