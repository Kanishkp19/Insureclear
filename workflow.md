# InsureClear — Pipeline Workflow

*End-to-end insurance policy understanding with Vectorless RAG + Universal Selector RL model.*

---

## Architecture Overview

```
User (Browser)
     │
     │  PDF Upload / Text Query
     ▼
React Frontend (Vite, port 5173)
     │
     │  POST /upload  ─── multipart PDF
     │  POST /query   ─── JSON question + session_id
     ▼
FastAPI Server (api_server.py, port 8000)
     │
     │  process_temp_pdf()  →  PageIndex SDK
     │  langgraph_app.invoke()
     ▼
LangGraph Pipeline (agent_pipeline.py)
  ┌──────────────────────────────────────────────┐
  │  [router_node]                               │
  │   • Classify domain (HEALTH / MOTOR / …)     │
  │   • Refine question for RL model             │
  │   • Detect comparison intent                 │
  │                                              │
  │  [rl_extraction_node]  ← UniversalInference  │
  │   • Scenario A: compare uploaded ↔ database  │
  │   • Scenario B: query uploaded doc only      │
  │   • Scenario C: query database only          │
  │   • Returns best clause + confidence score   │
  │                                              │
  │  [explainer_node]                            │
  │   • Gemini LLM explains / compares clauses   │
  │   • Grounded strictly in extracted text      │
  └──────────────────────────────────────────────┘
     │
     │  JSON { explanation, selected_clauses, domain }
     ▼
Frontend ChatPanel — renders answer + clause cards

```

---

## Setup & Commands

### 1 — Install backend dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` must include:
```
fastapi
uvicorn[standard]
python-multipart
python-dotenv
langgraph
google-genai
pageindex
torch
transformers
```

### 2 — Configure environment variables

Copy `.env.example` → `.env` and fill in your keys:

```bash
GEMINI_API_KEY=your_gemini_key_here
PAGEINDEX_API_KEY=your_pageindex_key_here
```

### 3 — Seed the database (optional)

Pre-process any baseline policy PDFs and save their vectorless trees as JSON to `backend/data/`:

```bash
cd backend
python process_policies.py
```

### 4 — Start the backend API server

```bash
cd backend
uvicorn api_server:server --host 0.0.0.0 --port 8000 --reload
```

The server loads the Universal Selector model on startup (~2–3 s).

### 5 — Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/upload` | Upload a PDF; returns `session_id` and node count |
| `POST` | `/query` | Ask a question; returns explanation + selected clauses |

### `POST /upload`

**Form data:** `file` (PDF), optional `session_id` query param.

```json
{
  "session_id": "abc-123",
  "message": "✅ 'policy.pdf' processed successfully.",
  "node_count": 47
}
```

### `POST /query`

**Request body:**
```json
{ "question": "Am I covered for theft?", "session_id": "abc-123" }
```

**Response:**
```json
{
  "session_id": "abc-123",
  "domain": "MOTOR",
  "refined_question": "Does the motor insurance policy cover theft or burglary of the insured vehicle?",
  "selected_clauses": [
    {
      "document_id": "User_Uploaded_Policy",
      "node_id": "3.4.1",
      "confidence_score": 0.8921,
      "text": "Section 3.4 — Loss or damage caused by theft…"
    }
  ],
  "explanation": "Yes. Under Section 3.4 of your uploaded policy, theft of the insured vehicle is covered…"
}
```

---

## Full Pipeline Walk-through

1. **Frontend** sends `POST /upload` with the user's PDF.
2. **`api_server.py`** saves the file temporarily, calls `process_temp_pdf()` which submits it to **PageIndex** and returns a vectorless JSON tree.
3. The tree is stored in an in-memory session store keyed to a `session_id` (UUID).
4. **Frontend** sends `POST /query` with the user's question + `session_id`.
5. **`api_server.py`** invokes the **LangGraph** pipeline with the question and the cached tree.
6. `router_node` → classifies domain, refines question, flags comparison intent.
7. `rl_extraction_node` → calls `UniversalInference.extract_payload`:
   - If comparison: ingests temp tree + loads database doc → returns top clause from each.
   - If upload only: ingests temp tree → returns top clause.
   - If no upload: loads database doc by domain → returns top clause.
8. `explainer_node` → Gemini LLM generates a grounded explanation from the extracted clause(s).
9. **API** returns `{ explanation, selected_clauses, domain, refined_question }` to the frontend.
10. **ChatPanel** renders the explanation and collapsible clause cards with confidence scores.

---

## Directory Structure

```
insure/
├── backend/
│   ├── api_server.py           ← FastAPI server (NEW)
│   ├── agent_pipeline.py       ← LangGraph pipeline (UPDATED)
│   ├── inference_universal.py  ← Universal Selector model (UPDATED)
│   ├── query_router.py         ← Standalone query preprocessor
│   ├── process_policies.py     ← Batch PDF → JSON indexer
│   ├── universal_selector/     ← Fine-tuned cross-encoder weights
│   ├── data/                   ← Pre-indexed policy JSON trees
│   └── .env                    ← API keys
│
└── frontend/
    └── src/
        ├── App.jsx             ← Root app (UPDATED — includes ChatPanel)
        ├── components/
        │   ├── ChatPanel.jsx   ← Live AI chat UI (NEW)
        │   └── …
        └── utils/
            └── api.js          ← API service layer (NEW)
```

---

## Notes

- Session data is held **in-memory** only — restarting the server clears all uploaded documents.
- The Universal Selector model (`./universal_selector/`) must be present. This directory contains the fine-tuned cross-encoder weights (`model.safetensors`, tokenizer files).
- CORS is set to `allow_origins=["*"]` for development. Restrict this in production.
