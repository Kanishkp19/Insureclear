"""
policy_translator.py
====================
Translates a PolicySummary JSON (produced by policy_summarizer.py) into Hindi
using Helsinki-NLP/opus-mt-en-hi — a fully LOCAL model from HuggingFace.

✅  No API key required
✅  No rate limits
✅  Works offline after first download (~300 MB, cached automatically)
✅  Already compatible with your existing torch + transformers dependencies

Pipeline:
  English summary JSON  →  translate_summary()  →  Hindi summary JSON
  (Same structure as input — every field translated, node_ids preserved)

FastAPI /translate endpoint snippet is at the bottom of this file.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────
# 1. LAZY MODEL LOADER  (loads once, reuses)
# ─────────────────────────────────────────────

_model     = None
_tokenizer = None
_lock      = threading.Lock()

MODEL_NAME = "Helsinki-NLP/opus-mt-en-hi"


def _load_model():
    """Load the MarianMT model once and cache it in module-level globals."""
    global _model, _tokenizer
    if _model is not None:
        return  # already loaded

    with _lock:
        if _model is not None:
            return  # double-checked locking

        print("   [translator] Loading Helsinki-NLP/opus-mt-en-hi model...")
        print("   [translator] First run will download ~300 MB — cached after that.")

        from transformers import MarianMTModel, MarianTokenizer

        _tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
        _model     = MarianMTModel.from_pretrained(MODEL_NAME)
        _model.eval()

        print("   [translator] Model loaded and ready.")


# ─────────────────────────────────────────────
# 2. CORE TRANSLATION HELPER
# ─────────────────────────────────────────────

# MarianMT handles up to 512 tokens per segment.
# Insurance sentences are long so we split on sentence boundaries
# and batch them to avoid truncation and keep quality high.

_SENT_SPLIT = re.compile(r'(?<=[।.!?])\s+')


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences; keep chunks ≤ 400 characters for safety."""
    raw = _SENT_SPLIT.split(text.strip())
    chunks: List[str] = []
    current = ""
    for sent in raw:
        if len(current) + len(sent) < 400:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks or [text]


def translate_text(text: str) -> str:
    """
    Translate a single English string to Hindi.
    Handles long text by splitting into sentence chunks.
    Returns the original text unchanged if it's empty or None.
    """
    if not text or not text.strip():
        return text

    _load_model()

    import torch

    sentences = _split_into_sentences(text)

    translated_parts: List[str] = []
    for chunk in sentences:
        inputs = _tokenizer(
            [chunk],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        )
        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                num_beams=4,           # beam search for better quality
                max_length=512,
                early_stopping=True,
            )
        decoded = _tokenizer.decode(outputs[0], skip_special_tokens=True)
        translated_parts.append(decoded)

    return " ".join(translated_parts)


def translate_list(items: List[str]) -> List[str]:
    """Translate a list of strings (used for watch_out_for bullets)."""
    if not items:
        return items
    _load_model()

    import torch

    # Batch all bullets in one model call for speed
    inputs = _tokenizer(
        items,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256,
    )
    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            num_beams=4,
            max_length=256,
            early_stopping=True,
        )
    return [_tokenizer.decode(o, skip_special_tokens=True) for o in outputs]


# ─────────────────────────────────────────────
# 3. MAIN PUBLIC FUNCTION
# ─────────────────────────────────────────────

def translate_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a full PolicySummary dict (from policy_summarizer.summarize_policy_tree)
    into Hindi. Returns a new dict with identical structure — all string fields
    translated, all non-string fields (node_id, page, total_clauses, doc_id) kept as-is.

    Parameters
    ----------
    summary : dict
        The JSON-serialisable dict returned by summarize_policy_tree().

    Returns
    -------
    dict  — same structure, all text fields in Hindi.

    Example input / output structure
    ---------------------------------
    Input:
    {
        "doc_id":        "pi-abc123",
        "overview":      "This policy covers...",
        "total_clauses": 22,
        "clauses": [
            {
                "node_id":       "0001",
                "clause_name":   "Death Benefit Payout",
                "plain_english": "If you pass away...",
                "watch_out_for": ["No payout if suicide...", "..."],
                "page":          1
            },
            ...
        ]
    }

    Output: identical shape, all text values in Hindi.
    """
    print("\n   [translator] Starting Hindi translation of policy summary...")

    translated: Dict[str, Any] = {
        "doc_id":        summary.get("doc_id"),
        "total_clauses": summary.get("total_clauses", 0),
        "language":      "hi",      # tag so frontend knows this is Hindi
        "language_name": "हिन्दी",
    }

    # ── Translate overview ────────────────────────────────────────────────────
    print("   [translator] Translating overview...")
    translated["overview"] = translate_text(summary.get("overview", ""))

    # ── Translate each clause ─────────────────────────────────────────────────
    original_clauses: List[Dict] = summary.get("clauses", [])
    translated_clauses: List[Dict] = []

    for i, clause in enumerate(original_clauses, 1):
        print(f"   [translator] Clause {i}/{len(original_clauses)}: {clause.get('clause_name', '')}")

        translated_clause: Dict[str, Any] = {
            # Preserve metadata unchanged
            "node_id": clause.get("node_id"),
            "page":    clause.get("page"),

            # Translate text fields
            "clause_name":   translate_text(clause.get("clause_name", "")),
            "plain_english": translate_text(clause.get("plain_english", "")),
            "watch_out_for": translate_list(clause.get("watch_out_for", [])),
        }
        translated_clauses.append(translated_clause)

    translated["clauses"] = translated_clauses
    print("   [translator] Hindi translation complete.")
    return translated


# ─────────────────────────────────────────────
# 4. FASTAPI /translate ENDPOINT SNIPPET
# ─────────────────────────────────────────────
#
# Add these to your api_server.py:
#
# ── imports ──────────────────────────────────────────────────────────────────
#
#   from policy_translator import translate_summary
#
# ── endpoint ─────────────────────────────────────────────────────────────────
#
#   class TranslateRequest(BaseModel):
#       summary: dict           # The full JSON from /summarize
#       target_language: str = "hi"   # reserved for future languages
#
#   @server.post("/translate")
#   async def translate_endpoint(body: TranslateRequest):
#       """
#       Translate an English PolicySummary JSON into Hindi.
#       Pass the full JSON returned by /summarize as the 'summary' field.
#
#       Request body:
#           { "summary": { ...output from /summarize... } }
#
#       Response:
#           Same structure as /summarize output but all text fields in Hindi,
#           plus "language": "hi" and "language_name": "हिन्दी".
#       """
#       if body.target_language != "hi":
#           raise HTTPException(status_code=400, detail="Only 'hi' (Hindi) is supported currently.")
#
#       result = translate_summary(body.summary)
#       return JSONResponse(content=result)
#
# ─────────────────────────────────────────────────────────────────────────────
#
# ── requirements.txt additions (already in yours, just confirming) ───────────
#
#   torch
#   transformers
#   sentencepiece          ← ADD THIS if not already present (MarianMT needs it)
#
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────
# 5. QUICK LOCAL TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import json

    # Minimal mock summary to test the translator locally
    mock_summary = {
        "doc_id": "test-001",
        "overview": (
            "This is a pure term life insurance policy that provides a death benefit "
            "to your family if you pass away during the policy term. "
            "It has no maturity benefit and no surrender value for regular premium policies."
        ),
        "total_clauses": 2,
        "clauses": [
            {
                "node_id": "0001",
                "clause_name": "Death Benefit",
                "plain_english": (
                    "If you die during the policy term, your nominee receives the full "
                    "sum assured as a lump sum or in installments as chosen."
                ),
                "watch_out_for": [
                    "No payout if suicide occurs within 12 months of policy start.",
                    "Benefit amount depends on the option chosen at policy inception.",
                ],
                "page": 1,
            },
            {
                "node_id": "0002",
                "clause_name": "Maturity Benefit",
                "plain_english": (
                    "This policy pays nothing if you survive to the end of the policy term. "
                    "It is a pure protection plan, not a savings plan."
                ),
                "watch_out_for": [
                    "Zero maturity payout — you receive nothing if you outlive the policy.",
                ],
                "page": 1,
            },
        ],
    }

    print("Translating mock summary to Hindi...\n")
    result = translate_summary(mock_summary)

    print("\n" + "=" * 60)
    print("OVERVIEW (Hindi):")
    print(result["overview"])
    print(f"\nTotal clauses: {result['total_clauses']}")
    for c in result["clauses"]:
        print(f"\n[{c['node_id']}] {c['clause_name']}")
        print(f"  → {c['plain_english']}")
        for w in c["watch_out_for"]:
            print(f"  ⚠  {w}")