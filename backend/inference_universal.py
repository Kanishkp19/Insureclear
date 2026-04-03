import re
import json
import torch
import glob
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ══════════════════════════════════════════════════════════════════════════════
#  UNIVERSAL TEXT RE-CHUNKER
# ══════════════════════════════════════════════════════════════════════════════

_RECHUNK_MIN_LEN = 300
_CHUNK_MIN_LEN   = 80

_SECTION_PATTERNS = [
    # Rider-style: "R1.", "R4. Diet Consultation Rider"
    re.compile(r'(?m)^(R\d{1,2}\.\s+[A-Z][^\n]{3,80})'),
    # Numbered clauses at line start: "1.", "2.1", "3.4.1  Title"
    re.compile(r'(?m)^(\d{1,2}(?:\.\d{1,2}){0,2}\.?\s+[A-Z][^\n]{3,80})'),
    # ALL-CAPS section headings common in insurance policies
    re.compile(r'(?m)^([A-Z][A-Z\s\-]{5,60})$'),
    # Markdown headers: "## Section" or "**Section**"
    re.compile(r'(?m)^(?:#{1,4}\s+|(?:\*\*))([A-Z][^\n*]{3,80})(?:\*\*)?'),
]

# Noise penalty list — definition/disclaimer/preamble nodes match
# many keywords generically and pollute the top candidates sent to the
# cross-encoder. Hard-penalise them in pre-retrieval scoring.
_NOISE_PATH_KEYWORDS = {
    "definition", "definitions", "disclaimer", "disclaimers",
    "preamble", "general", "introduction", "schedule", "annexure",
}


def _find_split_positions(text: str):
    hits = {}
    for pattern in _SECTION_PATTERNS:
        for m in pattern.finditer(text):
            pos = m.start()
            if pos not in hits:
                hits[pos] = m.group(0).strip()
    return sorted(hits.items())


def _rechunk_text(parent_id: str, text: str, path_str: str) -> list:
    """
    Split a large text blob into fine-grained sub-nodes.
    Sub-nodes use ONLY their own header as path root, NOT the parent path.
    This prevents wrong nesting like "Section 3 > R1 > R4" — each rider
    gets its own clean path e.g. "R4. Diet Consultation Rider".

    IMPORTANT: The bracketed path prefix is stored in node["path"] only.
    node["text"] contains CLEAN text with NO bracket prefix so the
    cross-encoder receives exactly what it was trained on.
    """
    if len(text) < _RECHUNK_MIN_LEN:
        return []

    splits = _find_split_positions(text)
    if len(splits) < 2:
        return []

    sub_nodes = []
    for i, (start, header) in enumerate(splits):
        end   = splits[i + 1][0] if i + 1 < len(splits) else len(text)
        chunk = text[start:end].strip()

        if len(chunk) < _CHUNK_MIN_LEN:
            continue

        sub_path  = header
        sub_id    = f"{parent_id}_chunk_{i}"
        short_sum = chunk[:120].replace("\n", " ")

        sub_nodes.append({
            "id":      sub_id,
            # summary keeps the path label for human-readable logging only
            "summary": f"[{sub_path}] {short_sum}",
            # FIX: text is CLEAN — no bracketed prefix injected here
            # The cross-encoder only sees plain clause text, same as training
            "text":    chunk,
            "path":    sub_path.lower(),
        })

    return sub_nodes


# ══════════════════════════════════════════════════════════════════════════════

class UniversalInference:
    def __init__(self, model_path="./universal_selector", data_folder="./data/"):
        print(f"⏳ Loading Universal Selector Cross-Encoder from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model     = AutoModelForSequenceClassification.from_pretrained(
                             model_path, num_labels=1)
        self.model.eval()
        print("   ✅ Universal Selector loaded.")

        self.json_docs = {}
        for filepath in glob.glob(os.path.join(data_folder, "*.json")):
            doc_id = os.path.basename(filepath).replace(".json", "")
            with open(filepath, 'r', encoding='utf-8') as f:
                data  = json.load(f)
                nodes = []
                self._extract_nodes(data.get('result', data), nodes)
                self.json_docs[doc_id] = [n for n in nodes if n["id"] and n["text"]]

    # ──────────────────────────────────────────────────────────────────────────
    def _extract_nodes(self, data, nodes_list, current_path=None):
        if current_path is None:
            current_path = []

        if isinstance(data, list):
            for item in data:
                self._extract_nodes(item, nodes_list, current_path)

        elif isinstance(data, dict):
            section_title = data.get("title", data.get("header", ""))
            new_path      = current_path + [section_title] if section_title else current_path

            node_id = data.get("node_id", data.get("id"))
            if node_id:
                summary  = str(data.get("prefix_summary", data.get("summary", "")))
                raw_text = str(data.get("text", ""))
                if len(summary) < 5:
                    summary = raw_text[:100]

                path_str = " > ".join(new_path) if new_path else ""

                nodes_list.append({
                    "id":      str(node_id),
                    # summary keeps path label for logging
                    "summary": f"[{path_str}] {summary}" if path_str else summary,
                    # FIX: text is CLEAN — no bracketed path prefix
                    # Cross-encoder sees plain clause text only, same as training
                    "text":    raw_text,
                    "path":    path_str.lower(),
                })

                sub_nodes = _rechunk_text(str(node_id), raw_text, path_str)
                if sub_nodes:
                    print(f"   ✂️  Re-chunked node '{node_id}' → {len(sub_nodes)} sub-nodes")
                nodes_list.extend(sub_nodes)

            if "nodes" in data:
                self._extract_nodes(data["nodes"], nodes_list, new_path)

    # ──────────────────────────────────────────────────────────────────────────
    def ingest_tree(self, doc_id: str, tree_dict):
        nodes = []
        data_to_extract = (
            tree_dict.get('result', tree_dict)
            if isinstance(tree_dict, dict)
            else tree_dict
        )
        self._extract_nodes(data_to_extract, nodes)
        self.json_docs[doc_id] = [n for n in nodes if n["id"] and n["text"]]
        count = len(self.json_docs.get(doc_id, []))
        print(f"   🧠 [Universal Selector] Ingested '{doc_id}' — {count} nodes ready.")

    # ──────────────────────────────────────────────────────────────────────────
    def extract_payload(self, question: str, targets: list,
                        confidence_threshold: float = 0.15) -> dict:

        payload = {"user_question": question, "selected_clauses": []}

        resolved_ids = []
        for target in targets:
            if isinstance(target, dict):
                doc_id = target["doc_id"]
                self.ingest_tree(doc_id, target["tree"])
                resolved_ids.append(doc_id)
            else:
                resolved_ids.append(target)

        with torch.no_grad():
            for doc_id in resolved_ids:
                if doc_id not in self.json_docs:
                    payload["selected_clauses"].append({
                        "document_id":      doc_id,
                        "node_id":          "Error",
                        "confidence_score": 0.0,
                        "text":             "[ DOCUMENT NOT FOUND IN DATABASE ]"
                    })
                    continue

                nodes = self.json_docs[doc_id]

                # ── 1. VECTORLESS PRE-RETRIEVAL ───────────────────────────
                def compute_score(query: str, node: dict) -> float:
                    q        = query.lower()
                    # For scoring we still use path + summary for signal,
                    # but the cross-encoder will only see clean node["text"]
                    combined = (
                        node.get("summary", "").lower() + " " +
                        node.get("text",    "").lower() + " " +
                        node.get("path",    "").lower()
                    )
                    path_l = node.get("path", "").lower()

                    # Hard penalty for noise nodes (definitions, disclaimers)
                    if any(kw in path_l for kw in _NOISE_PATH_KEYWORDS):
                        return -10.0

                    exact = 5.0 if q in combined else 0.0

                    # Expanded stopwords — words like "policy", "cover", "rider"
                    # appear in every node and give zero signal
                    stopwords = {
                        "is", "the", "a", "an", "of", "in", "on",
                        "for", "to", "and", "or", "what", "my", "me",
                        "does", "do", "have", "has", "will", "can",
                        "policy", "cover", "covered", "rider",
                    }
                    kws = [w for w in q.split()
                           if w not in stopwords and len(w) > 2]

                    kw_score = sum(1.5 for w in kws if w in combined)

                    bigrams  = [f"{kws[i]} {kws[i+1]}" for i in range(len(kws) - 1)]
                    bg_score = sum(3.0 for bg in bigrams if bg in combined)

                    # High path weight so clause-specific nodes rank much higher
                    path_score = sum(4.0 for w in kws if w in path_l)

                    return exact + kw_score + bg_score + path_score

                scored = [(compute_score(question, n), n) for n in nodes]
                scored.sort(key=lambda x: x[0], reverse=True)

                # Only pass candidates with a positive pre-retrieval score
                # to the cross-encoder. Noise nodes (score <= 0) are excluded.
                top_candidates = (
                    [n for s, n in scored[:25] if s > 0]
                    or [n for _, n in scored[:10]]
                )

                print("\nTop candidates:")
                for score, n in scored[:5]:
                    print(f"  {score:.1f} → {n['summary'][:100]}")

                # ── 2. CROSS-ENCODER RANKING ──────────────────────────────
                # node["text"] is already clean (no bracket prefix) so we feed
                # it directly — no stripping needed anymore
                pairs  = [[question, n["text"]] for n in top_candidates]
                inputs = self.tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
                logits = self.model(**inputs).logits.squeeze(-1)
                probs  = torch.sigmoid(logits)
                if probs.dim() == 0:
                    probs = probs.unsqueeze(0)

                # No fallback — if the cross-encoder cannot find a confident
                # match above the threshold, we return nothing for this doc
                # and let the explainer node report "not found" cleanly.
                # This is honest: a wrong confident answer is worse than silence.
                added = 0
                for idx in torch.argsort(probs, descending=True):
                    if added >= 3:
                        break
                    score_val = round(probs[idx].item(), 4)

                    if score_val < confidence_threshold:
                        # Log the miss so you can diagnose model issues
                        print(f"   ℹ️  Cross-encoder max score {score_val:.4f} "
                              f"below threshold {confidence_threshold}. "
                              f"No clause selected for '{doc_id}'.")
                        break

                    payload["selected_clauses"].append({
                        "document_id":      doc_id,
                        "node_id":          top_candidates[idx]["id"],
                        "confidence_score": score_val,
                        "text":             top_candidates[idx]["text"],
                    })
                    added += 1

        return payload


# ── TEST ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    question = "Does my policy cover me if my car is stolen?"
    engine   = UniversalInference()
    payload  = engine.extract_payload(
                   question,
                   ["BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree"])
    print("\n" + "=" * 50)
    print(json.dumps(payload, indent=2))
    print("=" * 50 + "\n")