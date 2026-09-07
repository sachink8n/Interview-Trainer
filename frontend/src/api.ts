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
}

export interface SessionDetail {
  session_id: string;
  job_role: string;
  skills: string[];
  created_at: string;
  turns: Turn[];
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
}

export interface QuestionResponse {
  turn_id: number;
  turn_num: number;
  question: string;
}

export interface AnswerResponse {
  turn_id: number;
  score: number;
  strengths: string;
  weaknesses: string;
  feedback: string;
  follow_up_question: string;
}

export interface HistoryResponse {
  session_id: string;
  turns: Turn[];
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
): Promise<SessionStartResponse> {
  return request<SessionStartResponse>('/session/start', {
    method: 'POST',
    body: JSON.stringify({ session_id, job_role }),
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

/** Fetch all turns for a session (interview history). */
export async function getHistory(session_id: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/interview/history/${session_id}`);
}
