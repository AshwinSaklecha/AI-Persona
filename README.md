# Ashwin Persona

This repo is set up as a phased build for a production-style AI persona system:

- `backend/`: FastAPI backend with Gemini wrappers, FAISS-first vector storage, RAG retrieval, Cal.com integration, and evaluation logging
- `frontend/`: Next.js app with grounded chat UI, Vapi web voice controls, and a simple booking panel
- `data/sources/`: source-of-truth documents that feed the RAG pipeline
- `tests/backend/`: basic tests for chunking, retrieval, and vector search
- `docs/architecture.md`: backend-first architecture overview with Mermaid diagrams
- `docs/vapi-setup.md`: exact Vapi dashboard setup for web calls, phone calls, and tool wiring

## Current Milestone

Phase 1 is scaffolded:

- local source ingestion from resume and GitHub-derived docs
- chunking, embeddings, retrieval, prompt assembly, and fallback behavior
- `/api/chat`, `/api/ingest/rebuild`, `/api/availability`, `/api/book`, `/api/health`
- browser chat UI with speech-to-text and text-to-speech
- live Cal.com slot lookup and booking calls
- evaluation logging to `data/logs/events.jsonl`

Phase 2 adds:

- live GitHub ingestion via GitHub's public API into `data/sources/github/live/`
- repo README snapshots plus authored contribution PR summaries
- source URLs flowing through retrieval so the UI can link back to repo and PR pages
- `POST /api/ingest/github` to sync GitHub sources and optionally rebuild the vector index

Phase 3 adds:

- chat-driven booking flow inside `/api/chat`
- simple in-memory conversation state for scheduling
- exact-window parsing, live slot suggestions, slot selection, and booking confirmation through Cal.com
- clickable slot replies in the main chat UI

Phase 4 starts the voice pivot:

- Vapi Web SDK on the frontend instead of browser speech APIs
- `POST /api/vapi/tools` to let Vapi reuse the same grounded chat + booking backend
- `GET /api/vapi/preview` to preview the resolved Vapi server URL configuration
- `POST /api/vapi/sync` to create/update the Vapi function tool and patch the assistant/phone number once a public backend URL exists
- environment scaffolding for Vapi assistant, phone number, and shared-secret setup

## Setup

1. Copy `.env.example` to `.env`
2. Fill in Gemini, Cal.com, and Vapi credentials
3. Install backend dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Install frontend dependencies:

```bash
cd frontend
npm install
npm run dev
```

## Rebuild The Index

Once the backend is running and `GEMINI_API_KEY` is set:

```bash
curl -X POST http://localhost:8000/api/ingest/rebuild
```

The backend will also try to auto-build the index on startup if credentials are present and no index exists.

## Sync GitHub Sources

With `GITHUB_USERNAME` and at least one configured repo:

```bash
curl -X POST http://localhost:8000/api/ingest/github \
  -H "Content-Type: application/json" \
  -d "{\"rebuild_index\": true}"
```

This writes live GitHub-derived markdown files into `data/sources/github/live/` and, by default, rebuilds the FAISS index right after syncing.

## Tests

```bash
python -m pytest tests/backend -q
```

## Notes

- Answers about Ashwin are retrieval-grounded and fall back to `I don't know based on the information I have right now.` when context is weak.
- General tech answers are allowed, but they should be clearly separated by the prompt as general knowledge instead of lived experience.
- FAISS is the primary vector backend. A NumPy fallback exists so tests and local development stay usable if FAISS wheels are unavailable on the active Python version.
- For Vapi setup after deployment, use [docs/vapi-setup.md](/d:/AI Persona/docs/vapi-setup.md).
