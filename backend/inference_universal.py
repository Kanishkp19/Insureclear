import re
import json
import torch
import glob
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# ══════════════════════════════════════════════════════════════════════════════
#  UNIVERSAL TEXT RE-CHUNKER
#
#  WHY THIS EXISTS:
#  PageIndex (and most tree-builders) assign one node per top-level heading.
#  A 4-page document with 6 riders gets only 5 nodes because all rider text
#  is collapsed into one parent "Section 3" blob. The cross-encoder then
#  scores that giant blob and gets diluted / wrong results.
#
#  This module detects section boundaries INSIDE any node's text and creates
#  individual synthetic child-nodes for each sub-section automatically —
#  so every clause is independently searchable regardless of how coarsely
#  PageIndex chunked the original document.
# ══════════════════════════════════════════════════════════════════════════════

# Minimum characters a node text must have before we attempt re-chunking.
_RECHUNK_MIN_LEN = 300

# Minimum characters a resulting chunk must have to be worth indexing.
_CHUNK_MIN_LEN = 80

# Patterns that signal a new sub-section inside a text blob.
# Each captures the header text as group(0). Listed most→least specific.
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


def _find_split_positions(text: str):
    """
    Scan text with all patterns and return sorted (offset, header) pairs.
    Deduplicates so two patterns matching the same position keep only one.
    """
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
    Returns [] if nothing is worth splitting (text is already atomic).
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

        sub_path  = f"{path_str} > {header}" if path_str else header
        sub_id    = f"{parent_id}_chunk_{i}"
        short_sum = chunk[:120].replace("\n", " ")

        sub_nodes.append({
            "id":      sub_id,
            "summary": f"[{sub_path}] {short_sum}",
            "text":    f"[{sub_path}] {chunk}",
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
        """
        Recursively walk the PageIndex tree and populate nodes_list.

        For every node whose text is large enough to contain multiple
        sub-sections, _rechunk_text() creates fine-grained synthetic child
        nodes so even a coarsely chunked document gets per-clause indexing.

        Before fix: 4-page Mental Wellbeing PDF → 5 nodes (all riders in 1 blob)
        After fix:  same PDF → 5 + 6 sub-nodes = 11+ individually scored riders
        """
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
                summary = str(data.get("prefix_summary", data.get("summary", "")))
                text    = str(data.get("text", ""))
                if len(summary) < 5:
                    summary = text[:100]

                path_str         = " > ".join(new_path) if new_path else ""
                enriched_summary = f"[{path_str}] {summary}" if path_str else summary
                enriched_text    = f"[{path_str}] {text}"    if path_str else text

                # Keep the original parent node
                nodes_list.append({
                    "id":      str(node_id),
                    "summary": enriched_summary,
                    "text":    enriched_text,
                    "path":    path_str.lower(),
                })

                # ── UNIVERSAL RE-CHUNKER ──────────────────────────────────
                # Detect and split any sub-sections inside this node's text.
                # Works for ANY document structure — insurance riders, legal
                # clauses, medical sections, etc. — purely pattern-driven,
                # no hardcoding for specific document types.
                sub_nodes = _rechunk_text(str(node_id), text, path_str)
                if sub_nodes:
                    print(f"   ✂️  Re-chunked node '{node_id}' "
                          f"→ {len(sub_nodes)} sub-nodes")
                nodes_list.extend(sub_nodes)

            if "nodes" in data:
                self._extract_nodes(data["nodes"], nodes_list, new_path)

    # ──────────────────────────────────────────────────────────────────────────
    def ingest_tree(self, doc_id: str, tree_dict):
        """
        Dynamically load a vectorless tree into the in-memory index.
        Used for user-uploaded documents — no disk I/O required.
        """
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
        """
        Extract best clauses per document and return a structured payload.

        targets: list of
          str  → doc_id in pre-loaded on-disk index
          dict → {"doc_id": str, "tree": dict} → ingested on the fly
        """
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
                    combined = (
                        node.get("summary", "").lower() + " " +
                        node.get("text",    "").lower() + " " +
                        node.get("path",    "").lower()
                    )
                    path_l = node.get("path", "").lower()

                    exact    = 5.0 if q in combined else 0.0

                    stopwords = {"is","the","a","an","of","in","on",
                                 "for","to","and","or","what","my","me"}
                    kws      = [w for w in q.split()
                                if w not in stopwords and len(w) > 2]
                    kw_score = sum(1.5 for w in kws if w in combined)

                    bigrams  = [f"{kws[i]} {kws[i+1]}" for i in range(len(kws)-1)]
                    bg_score = sum(3.0 for bg in bigrams if bg in combined)

                    path_score = sum(2.5 for w in kws if w in path_l)

                    return exact + kw_score + bg_score + path_score

                scored = [(compute_score(question, n), n) for n in nodes]
                scored.sort(key=lambda x: x[0], reverse=True)
                top_candidates = [n for _, n in scored[:25]] or nodes[:25]

                print("\nTop candidates:")
                for score, n in scored[:5]:
                    print(f"  {score:.1f} → {n['summary'][:100]}")

                # ── 2. CROSS-ENCODER RANKING ──────────────────────────────
                pairs  = [[question, n['text']] for n in top_candidates]
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

                for idx in torch.argsort(probs, descending=True)[:3]:
                    payload["selected_clauses"].append({
                        "document_id":      doc_id,
                        "node_id":          top_candidates[idx]['id'],
                        "confidence_score": round(probs[idx].item(), 4),
                        "text":             top_candidates[idx]['text']
                    })

        return payload


# ── TEST ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    question = "Does my policy cover me if my car is stolen?"
    engine   = UniversalInference()
    payload  = engine.extract_payload(
                   question,
                   ["BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree"])
    print("\n" + "="*50)
    print(json.dumps(payload, indent=2))
    print("="*50 + "\n")