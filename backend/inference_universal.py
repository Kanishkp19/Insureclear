import glob
import json
import os
import re

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


_RECHUNK_MIN_LEN = 300
_CHUNK_MIN_LEN = 80
_DEFAULT_CONFIDENCE_THRESHOLD = 0.15
_FALLBACK_PRETRIEVAL_THRESHOLD = 3.0
_MIN_CONFIDENCE_FLOOR = 1e-6

_SECTION_PATTERNS = [
    re.compile(r"(?m)^(R\d{1,2}\.\s+[A-Z][^\n]{3,80})"),
    re.compile(r"(?m)^(\d{1,2}(?:\.\d{1,2}){0,2}\.?\s+[A-Z][^\n]{3,80})"),
    re.compile(r"(?m)^([A-Z][A-Z\s\-]{5,60})$"),
    re.compile(r"(?m)^(?:#{1,4}\s+|(?:\*\*))([A-Z][^\n*]{3,80})(?:\*\*)?"),
]

_NOISE_PATH_KEYWORDS = {
    "definition",
    "definitions",
    "disclaimer",
    "disclaimers",
    "preamble",
    "general",
    "introduction",
    "schedule",
    "annexure",
}


def _find_split_positions(text: str):
    hits = {}
    for pattern in _SECTION_PATTERNS:
        for match in pattern.finditer(text):
            pos = match.start()
            if pos not in hits:
                hits[pos] = match.group(0).strip()
    return sorted(hits.items())


def _rechunk_text(parent_id: str, text: str, path_str: str) -> list:
    """
    Split large clause blobs into smaller nodes while keeping clean clause text
    for the cross-encoder. Path labels stay in metadata only.
    """
    if len(text) < _RECHUNK_MIN_LEN:
        return []

    splits = _find_split_positions(text)
    if len(splits) < 2:
        return []

    sub_nodes = []
    for index, (start, header) in enumerate(splits):
        end = splits[index + 1][0] if index + 1 < len(splits) else len(text)
        chunk = text[start:end].strip()

        if len(chunk) < _CHUNK_MIN_LEN:
            continue

        sub_nodes.append(
            {
                "id": f"{parent_id}_chunk_{index}",
                "summary": f"[{header}] {chunk[:120].replace(chr(10), ' ')}",
                "text": chunk,
                "path": header.lower(),
            }
        )

    return sub_nodes


class UniversalInference:
    def __init__(self, model_path="./universal_selector", data_folder="./data/"):
        print(f"[loader] Loading Universal Selector Cross-Encoder from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=1,
        )
        self.model.eval()
        print("   [ok] Universal Selector loaded.")

        self.json_docs = {}
        for filepath in glob.glob(os.path.join(data_folder, "*.json")):
            doc_id = os.path.basename(filepath).replace(".json", "")
            with open(filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            nodes = []
            self._extract_nodes(data.get("result", data), nodes)
            self.json_docs[doc_id] = [node for node in nodes if node["id"] and node["text"]]

    def _extract_nodes(self, data, nodes_list, current_path=None):
        if current_path is None:
            current_path = []

        if isinstance(data, list):
            for item in data:
                self._extract_nodes(item, nodes_list, current_path)
            return

        if not isinstance(data, dict):
            return

        section_title = data.get("title", data.get("header", ""))
        new_path = current_path + [section_title] if section_title else current_path

        node_id = data.get("node_id", data.get("id"))
        if node_id:
            summary = str(data.get("prefix_summary", data.get("summary", "")))
            raw_text = str(data.get("text", ""))
            if len(summary) < 5:
                summary = raw_text[:100]

            path_str = " > ".join(new_path) if new_path else ""

            nodes_list.append(
                {
                    "id": str(node_id),
                    "summary": f"[{path_str}] {summary}" if path_str else summary,
                    "text": raw_text,
                    "path": path_str.lower(),
                }
            )

            sub_nodes = _rechunk_text(str(node_id), raw_text, path_str)
            if sub_nodes:
                print(f"   [chunk] Re-chunked node '{node_id}' -> {len(sub_nodes)} sub-nodes")
            nodes_list.extend(sub_nodes)

        if "nodes" in data:
            self._extract_nodes(data["nodes"], nodes_list, new_path)

    def ingest_tree(self, doc_id: str, tree_dict):
        nodes = []
        data_to_extract = tree_dict.get("result", tree_dict) if isinstance(tree_dict, dict) else tree_dict
        self._extract_nodes(data_to_extract, nodes)
        self.json_docs[doc_id] = [node for node in nodes if node["id"] and node["text"]]
        count = len(self.json_docs.get(doc_id, []))
        print(f"   [ingest] Universal Selector ingested '{doc_id}' - {count} nodes ready.")

    def extract_payload(
        self,
        question: str,
        targets: list,
        confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> dict:
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
                    payload["selected_clauses"].append(
                        {
                            "document_id": doc_id,
                            "node_id": "Error",
                            "confidence_score": 0.0,
                            "text": "[ DOCUMENT NOT FOUND IN DATABASE ]",
                        }
                    )
                    continue

                nodes = self.json_docs[doc_id]

                def compute_score(query: str, node: dict) -> float:
                    query_lower = query.lower()
                    combined = (
                        node.get("summary", "").lower()
                        + " "
                        + node.get("text", "").lower()
                        + " "
                        + node.get("path", "").lower()
                    )
                    path_lower = node.get("path", "").lower()

                    if any(keyword in path_lower for keyword in _NOISE_PATH_KEYWORDS):
                        return -10.0

                    exact = 5.0 if query_lower in combined else 0.0

                    stopwords = {
                        "is",
                        "the",
                        "a",
                        "an",
                        "of",
                        "in",
                        "on",
                        "for",
                        "to",
                        "and",
                        "or",
                        "what",
                        "my",
                        "me",
                        "does",
                        "do",
                        "have",
                        "has",
                        "will",
                        "can",
                        "policy",
                        "cover",
                        "covered",
                        "rider",
                    }
                    keywords = [
                        word for word in query_lower.split() if word not in stopwords and len(word) > 2
                    ]

                    keyword_score = sum(1.5 for word in keywords if word in combined)
                    bigrams = [
                        f"{keywords[index]} {keywords[index + 1]}"
                        for index in range(len(keywords) - 1)
                    ]
                    bigram_score = sum(3.0 for bigram in bigrams if bigram in combined)
                    path_score = sum(4.0 for word in keywords if word in path_lower)

                    return exact + keyword_score + bigram_score + path_score

                scored = [(compute_score(question, node), node) for node in nodes]
                scored.sort(key=lambda item: item[0], reverse=True)

                top_candidate_pairs = [(score, node) for score, node in scored[:25] if score > 0] or scored[:10]
                top_candidates = [node for _, node in top_candidate_pairs]
                top_candidate_scores = [float(score) for score, _ in top_candidate_pairs]

                print("\nTop candidates:")
                for score, node in scored[:5]:
                    print(f"  {score:.1f} -> {node['summary'][:100]}")

                pairs = [[question, node["text"]] for node in top_candidates]
                inputs = self.tokenizer(
                    pairs,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )
                logits = self.model(**inputs).logits.squeeze(-1)
                if logits.dim() == 0:
                    logits = logits.unsqueeze(0)

                # The package metadata says the default activation is Identity.
                # That does not change the loaded classifier head; it just means
                # the original SentenceTransformers wrapper exposed raw scores.
                # We rank by raw logit and use sigmoid only as a bounded score.
                probs = torch.sigmoid(logits)

                ranked_candidates = []
                for idx_tensor in torch.argsort(logits, descending=True):
                    idx = idx_tensor.item()
                    ranked_candidates.append(
                        {
                            "document_id": doc_id,
                            "node_id": top_candidates[idx]["id"],
                            "confidence_score": max(
                                float(probs[idx].item()),
                                _MIN_CONFIDENCE_FLOOR,
                            ),
                            "raw_model_score": float(logits[idx].item()),
                            "retrieval_score": top_candidate_scores[idx],
                            "text": top_candidates[idx]["text"],
                        }
                    )

                added = 0
                for candidate in ranked_candidates:
                    if added >= 3:
                        break

                    if candidate["confidence_score"] < confidence_threshold:
                        continue

                    candidate["selection_reason"] = "threshold_pass"
                    payload["selected_clauses"].append(candidate)
                    added += 1

                if added == 0 and ranked_candidates:
                    best_candidate = dict(ranked_candidates[0])
                    if best_candidate["retrieval_score"] >= _FALLBACK_PRETRIEVAL_THRESHOLD:
                        best_candidate["fallback"] = True
                        best_candidate["selection_reason"] = "retrieval_fallback"
                        payload["selected_clauses"].append(best_candidate)
                        print(
                            f"   [info] Max model score {best_candidate['confidence_score']:.4f} "
                            f"was below threshold {confidence_threshold}, but keeping top "
                            f"candidate for '{doc_id}' via retrieval fallback "
                            f"(retrieval={best_candidate['retrieval_score']:.1f}, "
                            f"logit={best_candidate['raw_model_score']:.4f})."
                        )
                    else:
                        print(
                            f"   [info] Cross-encoder max score "
                            f"{best_candidate['confidence_score']:.4f} below threshold "
                            f"{confidence_threshold}, and retrieval support "
                            f"{best_candidate['retrieval_score']:.1f} was not strong enough "
                            f"for '{doc_id}'. No clause selected."
                        )

        return payload


if __name__ == "__main__":
    question = "Does my policy cover me if my car is stolen?"
    engine = UniversalInference()
    payload = engine.extract_payload(
        question,
        ["BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree"],
    )
    print("\n" + "=" * 50)
    print(json.dumps(payload, indent=2))
    print("=" * 50 + "\n")
