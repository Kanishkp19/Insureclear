// src/utils/api.js
// Central API service for communicating with the InsureClear FastAPI backend

const API_BASE = "http://localhost:8000";

/**
 * Upload a PDF document to be processed by the vectorless RAG pipeline.
 * Returns { session_id, message, node_count }
 */
export async function uploadDocument(file, sessionId = null) {
  const formData = new FormData();
  formData.append("file", file);

  const url = sessionId
    ? `${API_BASE}/upload?session_id=${encodeURIComponent(sessionId)}`
    : `${API_BASE}/upload`;

  const res = await fetch(url, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

/**
 * Send a question through the full pipeline.
 * Router → Universal Selector → Explainer
 * Returns { session_id, domain, refined_question, selected_clauses, explanation }
 */
export async function queryPipeline(question, sessionId = null) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

/**
 * Simple liveness check
 */
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
