"""
explainer.py
------------
Explanation layer for InsureClear.

Sits directly after the RL system in the pipeline:

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

# Lazy-initialized Groq client
_client = None

def get_groq_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            # Fallback for debugging, though it should be in .env
            raise ValueError("GROQ_API_KEY not found in environment. Please check your .env file.")
        _client = Groq(api_key=api_key)
    return _client

MODEL  = "llama-3.3-70b-versatile"


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

_CHATBOT_SYSTEM = """
You are a friendly insurance advisor in a live chat.
The user has asked a question. Our system has already pulled the exact clause
from their policy document.

Your job:
  • Start with YES or NO (or "it depends") in your very first sentence.
  • Explain in simple everyday English — zero legal jargon.
  • Name the section so the user can find it in their document.
  • If anything is excluded or conditional, say it clearly — do not soften it.
  • If no relevant clause was found, say so honestly and advise them to call
    their insurer.
  • Keep the reply under 120 words.
  • Tone: warm, direct, like a trusted friend who knows insurance.
"""


def explain_query_answer(rl_output: dict) -> dict:
    """
    Convert RL system output into a plain-English chatbot answer.

    Parameters
    ----------
    rl_output : dict
        The exact JSON dict produced by the RL system, shaped like:
        {
          "user_question": "Does my policy cover me if my car is stolen?",
          "selected_clauses": [
            {
              "document_id": "BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree",
              "node_id": "0002",
              "confidence_score": 0.95,
              "text": "SECTION I — ... by burglary housebreaking or theft ..."
            },
            ...
          ]
        }

    Returns
    -------
    dict:
        answer        str   plain-English reply for the user
        verdict       str   "covered" | "not_covered" | "conditional" | "not_found"
        confidence    str   "high" | "medium" | "low"
        section_ref   str   section name pulled from the best clause
        source_doc    str   document the answer came from
        needs_review  bool  True when best clause score < 0.60
    """
    question = rl_output.get("user_question", "")
    clauses  = rl_output.get("selected_clauses", [])

    # ── pick the best valid clause ────────────────────────────────────────────
    valid = [
        c for c in clauses
        if "NO RELEVANT CLAUSE" not in c.get("text", "").upper()
        and c.get("confidence_score", 0) > 0.0
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
    source_doc  = (
        best["document_id"]
        .replace("_tree", "")
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )
    node_id     = best.get("node_id", "N/A")
    section_ref = _extract_section_ref(clause_text)

    # ── call Groq ─────────────────────────────────────────────────────────────
    user_prompt = f"""
User's question: "{question}"

Our system retrieved this clause from the policy document.
Document  : {source_doc}
Node      : {node_id}
Confidence: {score:.0%}

Clause text:
\"\"\"{clause_text}\"\"\"

Write a short plain-English chatbot reply that:
1. Directly answers YES or NO to the user's question.
2. Explains which part of the clause supports this (in simple words).
3. Names the section so the user can check their document.
4. Calls out any conditions or exceptions clearly.
"""

    answer = _call_groq(_CHATBOT_SYSTEM, user_prompt, max_tokens=300)

    return {
        "answer":       answer,
        "verdict":      _infer_verdict(answer, clause_text),
        "confidence":   "high" if score >= 0.80 else ("medium" if score >= 0.60 else "low"),
        "section_ref":  section_ref,
        "source_doc":   source_doc,
        "needs_review": score < 0.60,
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
    """
    Summarise a full policy document in plain English.

    Parameters
    ----------
    policy_name : str
        Human-readable name for this policy.
    clauses : list[dict]
        All clause dicts from the RL system for this document.
        Each dict must have at minimum: { "node_id", "confidence_score", "text" }

    Returns
    -------
    dict:
        policy_name      str
        one_line         str   one-sentence summary
        what_is_covered  str
        what_is_not      str
        watch_out        str   dangerous surprises
        full_summary     str   complete Groq response
    """
    # use strongest clauses; fall back to all if nothing clears 0.60
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
    m = re.search(r"(section\s[\w\.]+|clause\s[\w\.]+)", clause_text, re.IGNORECASE)
    if m:
        return m.group(0).strip()
    return clause_text[:60].rstrip() + ("…" if len(clause_text) > 60 else "")


def _infer_verdict(answer: str, clause_text: str) -> str:
    first = answer.lower()[:60]
    if any(w in first for w in ["yes,", "yes.", "yes —", "yes!"]):
        return "covered"
    if any(w in first for w in ["no,", "no.", "no —", "not covered", "unfortunately"]):
        return "not_covered"
    if any(w in first for w in ["it depends", "conditionally", "partially"]):
        return "conditional"
    # fallback: check clause text polarity
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