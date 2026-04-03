from dotenv import load_dotenv
load_dotenv()

import os
import json
import uuid
import tempfile
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Import the compiled LangGraph pipeline and temp-file processor
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Session management is handled by agent_pipeline._session_store
# ---------------------------------------------------------------------------
from agent_pipeline import (
    app as langgraph_app, 
    process_temp_pdf, 
    get_temp_tree, 
    set_temp_tree,
    get_session,
    clear_temp_tree,
    _session_store
)

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
server = FastAPI(
    title="InsureClear API",
    description="Vectorless RAG + Universal Selector RL pipeline for insurance policy understanding.",
    version="1.0.0",
)

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Allow Vite dev server; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    session_id: str
    domain: str
    refined_question: str
    selected_clauses: list
    explanation: str


class UploadResponse(BaseModel):
    session_id: str
    message: str
    node_count: int


# ---------------------------------------------------------------------------
# Helper: get or create a session
# ---------------------------------------------------------------------------
def get_or_create_session(session_id: Optional[str]) -> str:
    sid = session_id if session_id and session_id in _session_store else str(uuid.uuid4())
    if sid not in _session_store:
        get_session(sid) # initializes the session
    return sid


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@server.get("/health")
def health():
    return {"status": "ok", "pipeline": "InsureClear v1.0"}


@server.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
):
    """
    Accepts a PDF uploaded by the user.
    Processes it via PageIndex → vectorless tree.
    Stores the tree in the session for downstream RL extraction.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    sid = get_or_create_session(session_id)

    # Save to a temp file so PageIndex SDK can read it
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        tree = process_temp_pdf(tmp_path)
    finally:
        os.remove(tmp_path)

    if not tree:
        raise HTTPException(status_code=500, detail="Failed to process PDF. Please try again.")

    set_temp_tree(sid, tree)

    # Count nodes for the response
    if isinstance(tree, list):
        node_count = len(tree)
    elif isinstance(tree, dict):
        res = tree.get("result", tree)
        if isinstance(res, list):
            node_count = len(res)
        elif isinstance(res, dict):
            node_count = len(res.get("nodes", []))
        else:
            node_count = 0
    else:
        node_count = 0

    return UploadResponse(
        session_id=sid,
        message=f"✅ Document '{file.filename}' processed successfully.",
        node_count=node_count,
    )


@server.post("/clear/{session_id}")
async def clear_document(session_id: str):
    """Clears the uploaded policy for this session."""
    clear_temp_tree(session_id)
    return {"message": "✅ Uploaded policy cleared."}


@server.post("/query", response_model=QueryResponse)
async def query_pipeline(body: QueryRequest):
    """
    Sends a user question through the full pipeline:
    Router → Universal Selector (RL) → Explainer
    If a session_id is provided and has a temp tree, it is included.
    """
    sid = get_or_create_session(body.session_id)
    
    # Build the LangGraph initial state
    initial_state = {
        "thread_id": sid,
        "messages": [{"role": "user", "content": body.question}],
    }

    # LangGraph thread config (ties memory to session)
    config = {"configurable": {"thread_id": sid}}
    
    print("DEBUG session_id received:", sid)
    print("DEBUG temp_tree in store:", get_temp_tree(sid) is not None)
    print("DEBUG all session keys:", list(_session_store.keys()))

    try:
        result = langgraph_app.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    rl_output = result.get("rl_output", {})

    return QueryResponse(
        session_id=sid,
        domain=result.get("current_domain", "UNKNOWN"),
        refined_question=result.get("refined_question", body.question),
        selected_clauses=rl_output.get("selected_clauses", []),
        explanation=result.get("final_explanation", ""),
    )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:server", host="0.0.0.0", port=8000, reload=True)
