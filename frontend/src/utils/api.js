// === API UTILITIES ===
const API = 'http://localhost:8000'

export async function uploadPDF(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(API + '/upload', { method: 'POST', body: form })
  return res.json() // { session_id, node_count }
}

export async function queryPolicy(question, sessionId) {
  const res = await fetch(API + '/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  })
  return res.json()
  // { explanation, selected_clauses, domain, refined_question }
}
