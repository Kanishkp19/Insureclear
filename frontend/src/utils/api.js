const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function uploadPDF(file, sessionId) {
  const formData = new FormData();
  formData.append("file", file);

  const url = new URL(`${API_BASE}/upload`);
  if (sessionId) {
    url.searchParams.set("session_id", sessionId);
  }

  const response = await fetch(url.toString(), {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function queryPolicy(question, sessionId) {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      session_id: sessionId || null,
    }),
  });

  if (!response.ok) {
    throw new Error(`Query failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchPolicyTree(sessionId) {
  const url = new URL(`${API_BASE}/tree`);
  if (sessionId) {
    url.searchParams.set("session_id", sessionId);
  }

  const response = await fetch(url.toString(), {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error(`Tree fetch failed with status ${response.status}`);
  }

  return response.json();
}
