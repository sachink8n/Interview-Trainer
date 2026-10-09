# Interview Trainer

Interview Trainer is an AI-powered mock interview application. It uses a React and TypeScript frontend for the interview experience and a FastAPI backend for resume processing, session management, question generation, answer evaluation, speech transcription, and focus tracking.

## Project Architecture

```text
interview-trainer/
├── backend/
│   ├── main.py                    # FastAPI application and startup lifecycle
│   ├── agent.py                   # Question generation and answer evaluation
│   ├── config.py                  # Environment variables and application settings
│   ├── requirements.txt           # Python dependencies
│   ├── data/knowledge_base/       # RAG knowledge files for interview topics
│   ├── db/
│   │   ├── database.py            # Database initialization and connection
│   │   ├── crud.py                # Session and interview-turn persistence
│   │   └── schema.sql             # SQLite schema
│   ├── routers/
│   │   ├── resume.py              # Resume upload endpoint
│   │   ├── session.py             # Interview-session endpoints
│   │   └── interview.py           # Questions, answers, transcription, focus, history
│   ├── services/
│   │   ├── evaluator.py           # Answer evaluation helpers
│   │   ├── focus_tracker.py       # Webcam-frame focus analysis
│   │   ├── granite.py             # IBM watsonx Granite integration
│   │   ├── interview_state.py     # Interview state management
│   │   ├── prompt_builder.py      # LLM prompt construction
│   │   ├── rag.py                 # Knowledge-base indexing and retrieval
│   │   ├── resume_parser.py       # PDF text and skill extraction
│   │   ├── skill_gap.py           # Job-description skill-gap analysis
│   │   └── speech_to_text.py      # IBM Watson Speech-to-Text integration
│   └── uploads/                   # Uploaded resume files
├── frontend/
│   ├── package.json               # Node dependencies and scripts
│   └── src/
│       ├── api.ts                 # Typed client for the backend API
│       ├── App.tsx                # Frontend routes
│       ├── components/            # Shared UI, recorder, and focus tracker
│       └── pages/                 # Home, setup, interview, and results screens
└── README.md
```

### Request flow

1. The user uploads a PDF resume through the frontend.
2. The backend extracts the resume text and skills and returns a `session_id`.
3. The user supplies a job role and optional job description to start the session.
4. The backend uses the resume, job information, RAG context, and Granite to generate questions and evaluate answers.
5. The frontend can send audio for transcription and webcam frames for focus analysis during the interview.
6. Session turns and evaluation results are stored in SQLite and shown on the results page.

## Prerequisites

- Python 3.10 or newer
- Node.js and npm
- IBM watsonx credentials for question generation and answer evaluation
- IBM Watson Speech-to-Text credentials if voice transcription is used

## Backend Setup and Run

Open a terminal in the `backend` directory:

```bash
cd interview-trainer/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs at `http://localhost:8000`.

Useful backend URLs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

Run the backend from the `backend` directory so that its relative database, upload, and knowledge-base paths resolve correctly. On startup, the application initializes the database and builds the RAG index.

### Backend environment variables

Create a `.env` file in `backend/` when using the external IBM services:

```dotenv
WATSONX_API_KEY=your_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
IBM_STT_API_KEY=your_ibm_stt_api_key
IBM_STT_URL=your_ibm_stt_url
IBM_STT_MODEL=en-US_Multimedia
```

Optional settings include `DB_PATH`, `FOCUS_MAX_FRAME_BYTES`, `FOCUS_SMOOTHING`, `RAG_CHUNK_SIZE`, `RAG_TOP_K`, and `MAX_PREVIOUS_QUESTIONS`. Do not commit real API keys.

## Frontend Setup and Run

Open a second terminal in the `frontend` directory:

```bash
cd interview-trainer/frontend
npm install
npm run dev
```

The frontend is normally available at `http://localhost:5173`.

The API client uses `http://localhost:8000` by default. To use another backend URL, create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Other frontend commands:

```bash
npm run build    # Type-check and create a production build
npm run lint     # Run Oxlint
npm run preview  # Preview the production build locally
```

Frontend routes:

- `/` - Home page
- `/setup` - Resume upload and interview setup
- `/interview/:sessionId` - Live interview
- `/results/:sessionId` - Session results and history

## Exposed Backend API

All request and response bodies are JSON unless stated otherwise. File-upload endpoints use `multipart/form-data`.

### Health

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Returns `{ "status": "ok" }` when the backend is running. |

### Resume

| Method | Endpoint | Input | Purpose |
| --- | --- | --- |
| `POST` | `/resume/upload` | Multipart field `file` containing a PDF | Saves and parses a resume, extracts skills, creates a session ID, and returns a short text preview. |

Response fields: `session_id`, `skills`, and `resume_text_preview`.

### Session

| Method | Endpoint | Input | Purpose |
| --- | --- | --- |
| `POST` | `/session/start` | JSON: `session_id`, `job_role`, optional `job_description` | Attaches the role to the uploaded resume, analyzes skill gaps when a job description is supplied, and persists the session. |
| `GET` | `/session/{session_id}` | Path parameter `session_id` | Returns session metadata, job information, detected skills, skill-gap results, and all interview turns. |

### Interview

| Method | Endpoint | Input | Purpose |
| --- | --- | --- |
| `POST` | `/interview/question` | JSON: `session_id` | Generates and stores the next adaptive interview question. |
| `POST` | `/interview/answer` | JSON: `session_id`, `turn_id`, `answer` | Evaluates an answer and returns a score, strengths, weaknesses, feedback, a follow-up question, and an ideal model answer. |
| `POST` | `/interview/transcribe` | Multipart field `audio` containing a browser audio recording | Transcribes the recording with IBM Watson Speech-to-Text. |
| `POST` | `/interview/focus/frame` | Multipart fields `session_id` and image `frame` | Processes one webcam frame and returns a focus score, face-presence flag, and head-pose values. |
| `GET` | `/interview/history/{session_id}` | Path parameter `session_id` | Returns answered turns for a session. |

Question responses include `turn_id`, `turn_num`, `question`, and `updated_difficulty`. Focus responses include `focus_score`, `face_present`, `yaw`, and `pitch`.

## Error Handling

Errors use FastAPI's standard JSON format with a `detail` field. Common statuses include:

- `400` for invalid or empty input
- `404` when a session, resume, or turn cannot be found
- `422` when a resume cannot be parsed or a request fails validation
- `502` or `503` when an external IBM service fails or is unavailable

## Development Notes

- The backend currently allows CORS requests from all origins for local development.
- Resume files, the SQLite database, and generated local indexes are runtime data and should not be committed.
- Keep the backend and frontend running in separate terminals during development.