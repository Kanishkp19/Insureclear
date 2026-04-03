"""
explainer.py
------------
Explanation layer for InsureClear.

    RL System JSON output  →  explainer.py  →  plain-English answer

Model : Groq — llama-3.3-70b-versatile (free, 14,400 req/day)
Key   : https://console.groq.com/keys   →   export GROQ_API_KEY=...

Two functions:
  explain_query_answer(rl_output)          — answers a user question
  summarise_policy(policy_name, clauses)   — explains a full policy doc
"""

import os
import re
from groq import Groq

_client = None

def get_groq_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment. Please check your .env file.")
        _client = Groq(api_key=api_key)
    return _client

MODEL = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────────────────────────────────────
def _call_groq(system: str, user: str, max_tokens: int = 600) -> str:
    client = get_groq_client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


# ══════════════════════════════════════════════════════════════════════════════
#  TASK 1 — CHATBOT: EXPLAIN A RETRIEVED CLAUSE TO THE USER
# ══════════════════════════════════════════════════════════════════════════════

# FIX 6: System prompt now asks the model to output a structured VERDICT line
# as the very first line of its response. This replaces the old fragile
# _infer_verdict() which guessed the verdict by scanning the first 60
# characters for patterns like "yes," or "no." — breaking if the LLM
# phrased its opening differently (e.g. "Absolutely, yes").
_CHATBOT_SYSTEM = """
You are a friendly insurance advisor in a live chat.
The user has asked a question. Our system has already pulled the exact clause
from their policy document.

Your job:
  • On the VERY FIRST LINE write exactly one of:
      VERDICT: covered
      VERDICT: not_covered
      VERDICT: conditional
      VERDICT: not_found
    (nothing else on that line)
  • Then on a new line, start your reply to the user.
  • Begin your reply with YES, NO, or "It depends" in the first sentence.
  • Explain in simple everyday English — zero legal jargon.
  • Name the section so the user can find it in their document.
  • If anything is excluded or conditional, say it clearly — do not soften it.
  • If no relevant clause was found, say so honestly and advise them to call
    their insurer.
  • Keep the reply under 150 words.
  • Tone: warm, direct, like a trusted friend who knows insurance.
"""


def explain_query_answer(rl_output: dict) -> dict:
    """
    Convert RL system output into a plain-English chatbot answer.

    Returns
    -------
    dict:
        answer        str   plain-English reply for the user
        verdict       str   "covered" | "not_covered" | "conditional" | "not_found"
        confidence    str   "high" | "medium" | "low"
        section_ref   str   section name pulled from the best clause
        source_doc    str   document the answer came from
        needs_review  bool  True when best clause score < 0.60 or fallback used
    """
    question = rl_output.get("user_question", "")
    clauses  = rl_output.get("selected_clauses", [])

    # ── pick the best valid clause ────────────────────────────────────────────
    valid = [
        c for c in clauses
        if "NO RELEVANT CLAUSE" not in c.get("text", "").upper()
        and c.get("confidence_score", 0) >= 0.0
    ]
    valid.sort(key=lambda c: c.get("confidence_score", 0), reverse=True)

    if not valid:
        return {
            "answer": (
                "I wasn't able to find a specific clause in your policy for this question. "
                "That doesn't necessarily mean it's not covered — our system may not have "
                "retrieved the right section. Please contact your insurer directly to confirm."
            ),
            "verdict":      "not_found",
            "confidence":   "low",
            "section_ref":  "Unknown",
            "source_doc":   "Unknown",
            "needs_review": True,
        }

    best        = valid[0]
    clause_text = best["text"]
    score       = best["confidence_score"]
    is_fallback = best.get("fallback", False)

    source_doc = (
        best["document_id"]
        .replace("_tree", "")
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )
    node_id     = best.get("node_id", "N/A")

    # FIX 7: Improved section ref extraction that handles the bracket-path
    # format produced by the re-chunker e.g. "[R4. Diet Consultation Rider] ..."
    # The old regex only matched "section 3" or "clause 2.1" style strings
    # and silently fell back to the first 60 chars (the path prefix itself).
    section_ref = _extract_section_ref(clause_text)

    # Tell the model to hedge if retrieval was uncertain
    confidence_note = (
        "⚠️ Note: The system had low confidence retrieving this clause. "
        "Please reflect that uncertainty in your answer."
        if is_fallback or score < 0.30 else ""
    )

    user_prompt = f"""
User's question: "{question}"

Our system retrieved this clause from the policy document.
Document  : {source_doc}
Node      : {node_id}
Confidence: {score:.1%}
{confidence_note}

Clause text:
\"\"\"{clause_text}\"\"\"

Write your response following the system instructions exactly.
Remember: first line must be VERDICT: <value>, then your reply on the next line.
"""

    raw_answer = _call_groq(_CHATBOT_SYSTEM, user_prompt, max_tokens=3500)

    # FIX 6: Parse the structured VERDICT line instead of guessing from text.
    verdict, answer = _parse_verdict_and_answer(raw_answer, clause_text)

    return {
        "answer":       answer,
        "verdict":      verdict,
        "confidence":   "high" if score >= 0.80 else ("medium" if score >= 0.60 else "low"),
        "section_ref":  section_ref,
        "source_doc":   source_doc,
        "needs_review": score < 0.60 or is_fallback,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  TASK 2 — DOCUMENT SUMMARY: EXPLAIN THE FULL POLICY IN PLAIN ENGLISH
# ══════════════════════════════════════════════════════════════════════════════

_SUMMARY_SYSTEM = """
You are an insurance advisor explaining a policy to someone who has never
read a policy document before — keep it genuinely simple.

Rules:
  • Plain, friendly English. No legal phrases.
  • Cover: what IS protected, what is NOT protected, any waiting periods
    or sub-limits, and the 2-3 things most likely to surprise someone
    when they try to file a claim.
  • Short paragraphs — real sentences, not bullet walls.
  • End with a "Watch Out" block for the most dangerous exclusions.
  • Never copy the legal text word-for-word. Rewrite in your own words.
  • Do not add anything not present in the clauses provided.
"""


def summarise_policy(policy_name: str, clauses: list) -> dict:
    strong = [c for c in clauses if c.get("confidence_score", 0) >= 0.60] or clauses

    clause_block = "\n\n".join(
        f"[Node {c.get('node_id','?')} | {c.get('confidence_score',0):.2f}]\n{c['text']}"
        for c in strong[:15]
    )

    user_prompt = f"""
Policy: {policy_name}

Extracted clauses:
{clause_block}

Write a plain-English summary with these four clearly labelled sections:
1. ONE-LINE SUMMARY
2. WHAT IS COVERED
3. WHAT IS NOT COVERED
4. WATCH OUT
"""

    raw      = _call_groq(_SUMMARY_SYSTEM, user_prompt, max_tokens=900)
    sections = _parse_sections(raw, [
        "ONE-LINE SUMMARY",
        "WHAT IS COVERED",
        "WHAT IS NOT COVERED",
        "WATCH OUT",
    ])

    return {
        "policy_name":     policy_name,
        "one_line":        sections.get("ONE-LINE SUMMARY", ""),
        "what_is_covered": sections.get("WHAT IS COVERED", ""),
        "what_is_not":     sections.get("WHAT IS NOT COVERED", ""),
        "watch_out":       sections.get("WATCH OUT", ""),
        "full_summary":    raw,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _extract_section_ref(clause_text: str) -> str:
    """
    FIX 7: Handles three formats in priority order:

    1. Bracket-path from re-chunker: "[R4. Diet Consultation Rider] ..."
       → returns last segment e.g. "R4. Diet Consultation Rider"

    2. Inline section/clause reference: "Section 3", "Clause 2.1"
       → returns matched text

    3. Fallback: first 60 chars of text
    """
    # Format 1: bracketed path prefix like "[R4. Diet Consultation Rider]"
    m = re.match(r'^\[([^\]]+)\]', clause_text.strip())
    if m:
        path  = m.group(1)
        parts = [p.strip() for p in path.split(">")]
        return parts[-1]

    # Format 2: inline section/clause keyword
    m = re.search(r'(section\s[\w\.]+|clause\s[\w\.]+)', clause_text, re.IGNORECASE)
    if m:
        return m.group(0).strip()

    # Format 3: fallback
    return clause_text[:60].rstrip() + ("…" if len(clause_text) > 60 else "")


def _parse_verdict_and_answer(raw: str, clause_text: str) -> tuple:
    """
    FIX 6: Extract the structured VERDICT line the model was asked to produce,
    then return the remaining lines as the user-facing answer.
    Falls back to heuristic if the model didn't follow the format.

    Returns (verdict_str, answer_str)
    """
    lines          = raw.strip().splitlines()
    valid_verdicts = {"covered", "not_covered", "conditional", "not_found"}

    if lines and lines[0].upper().startswith("VERDICT:"):
        raw_verdict = lines[0].split(":", 1)[1].strip().lower()
        verdict     = raw_verdict if raw_verdict in valid_verdicts else "covered"
        answer      = "\n".join(lines[1:]).strip()
        return verdict, answer

    # Fallback to heuristic if model ignored the format instruction
    return _infer_verdict_heuristic(raw, clause_text), raw


def _infer_verdict_heuristic(answer: str, clause_text: str) -> str:
    """Kept only as a fallback for _parse_verdict_and_answer."""
    first = answer.lower()[:80]
    if any(w in first for w in ["yes,", "yes.", "yes —", "yes!"]):
        return "covered"
    if any(w in first for w in ["no,", "no.", "no —", "not covered", "unfortunately"]):
        return "not_covered"
    if any(w in first for w in ["it depends", "conditionally", "partially"]):
        return "conditional"
    if any(p in clause_text.lower() for p in ["shall not", "not covered", "excluded", "no claim"]):
        return "not_covered"
    return "covered"


def _parse_sections(text: str, labels: list) -> dict:
    result, current, lines = {}, None, []
    for line in text.split("\n"):
        upper   = line.strip().upper()
        matched = False
        for label in labels:
            if label in upper:
                if current:
                    result[current] = "\n".join(lines).strip()
                current, lines, matched = label, [], True
                break
        if not matched and current:
            lines.append(line)
    if current:
        result[current] = "\n".join(lines).strip()
    return result