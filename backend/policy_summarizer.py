"""
policy_summarizer.py
--------------------
Converts a PageIndex vectorless JSON tree (from process_temp_pdf)
into a plain-English clause-by-clause summary using the Grok API.

Usage (standalone):
    from policy_summarizer import summarize_policy_tree
    result = summarize_policy_tree(tree_dict)

Usage (via FastAPI endpoint):
    POST /summarize  →  { session_id: "..." }
    Returns: { clauses: [...], policy_title: "...", session_id: "..." }
"""

import os
import json
import re
from typing import Any, Dict, List, Optional
from openai import OpenAI                 # xAI Grok uses the OpenAI-compatible SDK

# ---------------------------------------------------------------------------
# Client — Groq (OpenAI-compatible)
# ---------------------------------------------------------------------------
_groq_client: Optional[OpenAI] = None

def _get_client() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY is not set in your .env file.")
        _groq_client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _groq_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_IMG_RE = re.compile(r'!\[.*?\]\(.*?\)')

def _clean_text(text: str) -> str:
    """Strip markdown image tags and collapse extra whitespace."""
    text = _IMG_RE.sub('', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _extract_nodes(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    PageIndex trees come in two shapes:
      Shape A (from get_tree): { "result": [ { "title", "text", "node_id" }, ... ] }
      Shape B (from get_tree with node_summary=True): { "result": { "nodes": [...] } }
    Returns a flat list of node dicts either way.
    """
    result = tree.get("result", [])
    if isinstance(result, list):
        return result                       # Shape A — your pipeline produces this
    if isinstance(result, dict):
        return result.get("nodes", [])     # Shape B
    return []


def _build_clause_blocks(nodes: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Turn raw nodes into trimmed { title, text } pairs,
    skipping nodes that are empty or purely decorative.
    """
    clauses = []
    for node in nodes:
        title = (node.get("title") or "").strip()

        # prefer summary if present (already cleaned up by PageIndex)
        body = node.get("summary") or node.get("text") or ""
        body = _clean_text(body)

        # skip near-empty nodes (headers, blank pages, image-only nodes)
        if len(body) < 40:
            continue

        if not title:
            title = f"Section {node.get('node_id', '?')}"

        clauses.append({"title": title, "text": body})
    return clauses


# ---------------------------------------------------------------------------
# Core prompt — sent once per chunk
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are an insurance policy expert who specialises in explaining complex \
insurance documents to ordinary people with no legal or financial background.

You will receive a numbered list of policy clauses, each with a title and raw text.
For EVERY clause provided, produce a JSON object with exactly these three fields:

  "clause_name"   : copy the clause title verbatim
  "plain_english" : 2–4 sentences explaining what this clause means in \
simple everyday language a 16-year-old could understand. \
Avoid jargon. If a clause talks about a benefit, say exactly what the person gets. \
If it is a restriction, say clearly what is NOT covered.
  "watch_out_for" : a JSON array of 1–3 short strings, each highlighting \
something the policyholder must pay attention to — hidden conditions, exclusions, \
deadlines, monetary limits, situations that void a claim, or anything that could \
catch them off guard. If there is genuinely nothing to watch out for, return [].

Return ONLY a JSON array of these objects — no preamble, no markdown fences, \
no extra keys. The array must have exactly one object per clause, in the same order.
"""


def _build_user_prompt(clauses: List[Dict[str, str]]) -> str:
    lines = []
    for i, c in enumerate(clauses, 1):
        lines.append(f"--- CLAUSE {i}: {c['title']} ---")
        lines.append(c["text"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Groq call — with chunking for large policies
# ---------------------------------------------------------------------------
_MAX_CLAUSES_PER_CALL = 12   # safe chunk size — keeps each call within context limits

def _call_groq(clauses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Send one chunk to Groq and parse the returned JSON array."""
    client = _get_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(clauses)},
        ],
        temperature=0.2,                   # low temp → consistent structured output
    )

    raw = response.choices[0].message.content.strip()

    # strip accidental markdown fences Groq sometimes adds
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE).strip()
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Groq returned invalid JSON: {e}\n\nRaw output (first 500 chars):\n{raw[:500]}"
        )

    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON array from Groq, got: {type(parsed)}")

    return parsed


def _chunked_groq_call(clauses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Split large policies into chunks and merge results."""
    results = []
    total_chunks = (len(clauses) + _MAX_CLAUSES_PER_CALL - 1) // _MAX_CLAUSES_PER_CALL

    for chunk_idx, i in enumerate(range(0, len(clauses), _MAX_CLAUSES_PER_CALL), 1):
        chunk = clauses[i : i + _MAX_CLAUSES_PER_CALL]
        print(f"   [summarizer] Chunk {chunk_idx}/{total_chunks} — {len(chunk)} clauses...")
        chunk_result = _call_groq(chunk)
        results.extend(chunk_result)

    return results


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def summarize_policy_tree(tree: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a PageIndex JSON tree into a plain-English clause summary.

    Args:
        tree:  The raw dict returned by process_temp_pdf() or pi_client.get_tree().
               Must contain a "result" key with a list of nodes.

    Returns:
        {
            "policy_title":  str,           # inferred from first node title
            "total_clauses": int,
            "clauses": [
                {
                    "clause_name":   str,
                    "plain_english": str,
                    "watch_out_for": [str, ...]
                },
                ...
            ]
        }

    Raises:
        ValueError  if the tree is empty or Groq returns malformed output.
    """
    nodes = _extract_nodes(tree)
    if not nodes:
        raise ValueError(
            "No nodes found in the policy tree. "
            "Make sure the PageIndex upload completed before calling summarize."
        )

    clauses = _build_clause_blocks(nodes)
    if not clauses:
        raise ValueError(
            "All nodes were empty after cleaning — nothing to summarise. "
            "The PDF may be image-only or too short."
        )

    # Infer a human-friendly title from the first non-empty node
    policy_title = nodes[0].get("title", "Insurance Policy Summary").strip() or "Insurance Policy Summary"

    print(f"   [summarizer] '{policy_title}' — {len(clauses)} clauses to process.")

    summarized = _chunked_groq_call(clauses)

    print(f"   [summarizer] ✅ Complete — {len(summarized)} clauses summarised.")

    return {
        "policy_title":  policy_title,
        "total_clauses": len(summarized),
        "clauses":       summarized,
    }