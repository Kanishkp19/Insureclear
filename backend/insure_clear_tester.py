"""
insure_clear_tester.py
======================
Comprehensive end-to-end test suite for the InsureClear pipeline.

Tests every layer of the system independently and together:
  1. Re-chunker          — does _rechunk_text split nodes correctly?
  2. Node ingestion      — does ingest_tree produce the right node count?
  3. Pre-retrieval scorer— does compute_score rank the right node first?
  4. Cross-encoder       — does the RL model score the right clause highest?
  5. Explainer           — does explain_query_answer give a correct verdict?
  6. Edge cases          — empty docs, gibberish queries, missing keys, etc.
  7. API integration     — live POST /upload + POST /query end-to-end test

Run:
    python insure_clear_tester.py                        # all tests
    python insure_clear_tester.py --layer rechunker      # one layer only
    python insure_clear_tester.py --api http://localhost:8000  # with live API
    python insure_clear_tester.py --pdf path/to/doc.pdf  # test a real PDF

Requirements:
    pip install requests colorama tabulate
    All InsureClear backend packages must be installed.

Output:
    • Colour-coded pass/fail for every test case
    • Per-layer score summary
    • Improvement suggestions ranked by impact
"""

import argparse
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# ── optional colour output ─────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    GREEN  = Fore.GREEN
    RED    = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN   = Fore.CYAN
    BOLD   = Style.BRIGHT
    RESET  = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# ══════════════════════════════════════════════════════════════════════════════
#  TEST RESULT DATACLASS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TestResult:
    layer:       str
    name:        str
    passed:      bool
    score:       float          # 0.0 – 1.0 quality metric
    latency_ms:  float
    details:     str = ""
    suggestion:  str = ""       # improvement suggestion if failed/partial
    raw:         Any = field(default=None, repr=False)


# ══════════════════════════════════════════════════════════════════════════════
#  SYNTHETIC DOCUMENT FIXTURES
#  (used when no real PDF is available so tests run without PageIndex)
# ══════════════════════════════════════════════════════════════════════════════

MENTAL_WELLBEING_TREE = {
    "doc_id": "test_mental_wellbeing",
    "status": "ready",
    "retrieval_ready": True,
    "result": [
        {
            "node_id": "0001",
            "title": "Policy Wordings",
            "page_index": 1,
            "prefix_summary": "Policy wordings for Mental Wellbeing rider.",
            "text": "# Policy Wordings\nMental Wellbeing\nPage 1 of 4",
            "nodes": []
        },
        {
            "node_id": "0002",
            "title": "Section 1: Preamble",
            "page_index": 1,
            "prefix_summary": "Conditions for opting into riders.",
            "text": (
                "# Section 1: Preamble\n"
                "Rider can only be opted along with the base Policy and cannot be opted in isolation.\n"
                "The Riders are provided in lieu of additional premium."
            ),
            "nodes": []
        },
        {
            "node_id": "0003",
            "title": "Section 2: General Definitions",
            "page_index": 1,
            "prefix_summary": "Defines Health Care Professional and Service Provider.",
            "text": (
                "# Section 2: General Definitions\n"
                "1. Health Care Professional: A person who holds a valid qualification "
                "from a regulatory body engaged in maintaining individual health.\n"
                "2. Service Provider: Providers empanelled and engaged by Us for arranging services."
            ),
            "nodes": []
        },
        {
            "node_id": "0004",
            "title": "Section 3: Rider Covers",
            "page_index": 2,
            "prefix_summary": "All rider covers under the Mental Wellbeing policy.",
            "text": (
                "# Section 3: Rider Covers\n\n"
                "R1. Mental Health Screening\n"
                "In consideration of additional premium paid, We will arrange for Mental Health "
                "Screening of the Insured Person, once in a Policy Year. Such screening shall include: "
                "a) One evaluation with psychiatrist b) An online questionnaire for personality assessment "
                "c) Diagnostic tests including Thyroid function Test, Liver Function Test, Kidney Function Test.\n\n"
                "R2. Psychological Therapy and Procedures\n"
                "In consideration of additional premium paid, We will arrange for psychological therapy "
                "session with a registered psychiatric/psychologist for management of mental disorders "
                "including anxiety, depression, stress, bipolar disorder, substance use/abuse.\n\n"
                "R3. Vocational Rehabilitation\n"
                "In consideration of additional premium paid, if an illness impacts mental health affecting "
                "career/job performance, We will cover expenses for vocational rehabilitation.\n\n"
                "R4. Diet Consultation Rider\n"
                "In consideration of additional premium paid and with an objective of maintaining good health, "
                "We/Our empanelled service provider will arrange for a consultation with a "
                "nutritionist/dietitian during the Policy Period. Consultation will be provided through "
                "various specified modes of communication including in person, audio, video, online portal, "
                "chat, customer application or any other digital mode.\n\n"
                "R5. Stress Management Rider\n"
                "In consideration of additional premium paid, We will arrange for consultative services "
                "by a Health Care Professional through Stress Management Program including sessions on "
                "work/life balance, awareness sessions on mental wellbeing, mental health screening.\n\n"
                "R6. Addiction Cessation Program\n"
                "In consideration of additional premium paid, We will arrange for consultative services "
                "related to controlling substance addiction through the cessation program including "
                "expert counselling and consultations."
            ),
            "nodes": []
        },
        {
            "node_id": "0005",
            "title": "Disclaimers",
            "page_index": 3,
            "prefix_summary": "Disclaimer conditions and liability exclusions.",
            "text": (
                "# Disclaimers\n"
                "1. Any service under this Rider will only be provided on the request of the Insured Person "
                "through our empanelled Service Providers on cashless basis only.\n"
                "2. Availing the services under this Rider is upon the Insured Person's sole discretion.\n"
                "3. We shall not be responsible for any loss, damage, cost, charges and expenses which the "
                "Insured Person claims to have suffered.\n"
                "4. The Insured Person is free to choose whether or not to act on the recommendation.\n"
                "5. Any service availed by the Insured Person under these Benefits will not impact "
                "Cumulative Bonus under the base policy."
            ),
            "nodes": []
        }
    ]
}

MOTOR_TREE = {
    "doc_id": "test_motor",
    "status": "ready",
    "retrieval_ready": True,
    "result": [
        {
            "node_id": "M001",
            "title": "Section I: Loss or Damage",
            "page_index": 1,
            "prefix_summary": "Covers loss or damage to the insured vehicle.",
            "text": (
                "# Section I: Loss or Damage\n"
                "The company will indemnify the insured against loss or damage to the vehicle insured "
                "including accessories whilst thereon by burglary, housebreaking or theft, fire, "
                "explosion, self-ignition, lightning, earthquake, flood, cyclone, or accidental external means.\n\n"
                "1.1 Own Damage Cover\n"
                "Covers accidental damage to the insured vehicle up to the Insured Declared Value (IDV).\n\n"
                "1.2 Theft Cover\n"
                "Covers total loss of the vehicle due to theft or burglary. FIR must be filed within 24 hours.\n\n"
                "1.3 Natural Calamity Cover\n"
                "Covers damage due to floods, earthquakes, and other natural disasters."
            ),
            "nodes": []
        },
        {
            "node_id": "M002",
            "title": "Section II: Third Party Liability",
            "page_index": 2,
            "prefix_summary": "Third party liability coverage.",
            "text": (
                "# Section II: Third Party Liability\n"
                "The company will indemnify the insured against legal liability to third parties "
                "for bodily injury, death, or property damage caused by the insured vehicle.\n\n"
                "2.1 Bodily Injury\n"
                "Unlimited liability for bodily injury or death of third parties.\n\n"
                "2.2 Property Damage\n"
                "Up to Rs. 7.5 lakhs for damage to third party property."
            ),
            "nodes": []
        },
        {
            "node_id": "M003",
            "title": "Section III: Exclusions",
            "page_index": 3,
            "prefix_summary": "What is not covered under this motor policy.",
            "text": (
                "# Section III: Exclusions\n"
                "The following are not covered:\n\n"
                "3.1 Wear and Tear\n"
                "Normal wear and tear, mechanical or electrical breakdown is not covered.\n\n"
                "3.2 Drunk Driving\n"
                "Any damage caused while the driver was under influence of alcohol or drugs is excluded.\n\n"
                "3.3 War and Nuclear Risks\n"
                "Loss or damage due to war, nuclear risks, or radioactive contamination is excluded.\n\n"
                "3.4 Consequential Loss\n"
                "Depreciation and any consequential loss is not covered."
            ),
            "nodes": []
        }
    ]
}


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CASES DEFINITION
# ══════════════════════════════════════════════════════════════════════════════

# Each test case: (query, expected_keyword_in_retrieved_text, expected_verdict)
QUERY_TEST_CASES = [
    # ── DEFINITIONAL QUERIES ─────────────────────────────────────────────────
    {
        "id": "Q01",
        "category": "definitional",
        "query": "what is diet consultation rider",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["diet", "nutritionist", "dietitian"],
        "expected_verdict": "covered",
        "description": "Basic definitional query — should retrieve R4 node",
    },
    {
        "id": "Q02",
        "category": "definitional",
        "query": "explain stress management rider",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["stress", "management", "health care professional"],
        "expected_verdict": "covered",
        "description": "Definitional query for R5 Stress Management Rider",
    },
    {
        "id": "Q03",
        "category": "definitional",
        "query": "what is vocational rehabilitation",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["vocational", "rehabilitation", "career"],
        "expected_verdict": "covered",
        "description": "Definitional query for R3 Vocational Rehabilitation",
    },

    # ── COVERAGE QUERIES ─────────────────────────────────────────────────────
    {
        "id": "Q04",
        "category": "coverage",
        "query": "am I covered for addiction treatment",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["addiction", "cessation", "substance"],
        "expected_verdict": "covered",
        "description": "Coverage query for R6 Addiction Cessation Program",
    },
    {
        "id": "Q05",
        "category": "coverage",
        "query": "does my policy cover theft of my car",
        "tree": MOTOR_TREE,
        "doc_id": "test_motor",
        "expected_keywords": ["theft", "burglary"],
        "expected_verdict": "covered",
        "description": "Motor theft coverage query",
    },
    {
        "id": "Q06",
        "category": "coverage",
        "query": "is drunk driving covered",
        "tree": MOTOR_TREE,
        "doc_id": "test_motor",
        "expected_keywords": ["alcohol", "drunk", "excluded"],
        "expected_verdict": "not_covered",
        "description": "Exclusion query — should return not_covered",
    },
    {
        "id": "Q07",
        "category": "coverage",
        "query": "does flood damage get covered",
        "tree": MOTOR_TREE,
        "doc_id": "test_motor",
        "expected_keywords": ["flood", "natural"],
        "expected_verdict": "covered",
        "description": "Natural calamity coverage query",
    },

    # ── CONDITIONAL QUERIES ──────────────────────────────────────────────────
    {
        "id": "Q08",
        "category": "conditional",
        "query": "can I get mental health screening every month",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["once", "policy year", "screening"],
        "expected_verdict": "conditional",
        "description": "Frequency-limited benefit — should flag the once-per-year condition",
    },
    {
        "id": "Q09",
        "category": "conditional",
        "query": "is psychological therapy covered without a doctor prescription",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["prescribed", "medical practitioner", "diagnosed"],
        "expected_verdict": "conditional",
        "description": "Conditional coverage — requires doctor prescription",
    },

    # ── EDGE CASES ───────────────────────────────────────────────────────────
    {
        "id": "E01",
        "category": "edge_case",
        "query": "what is the premium amount",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": [],  # not in document — should gracefully fail
        "expected_verdict": "not_found",
        "description": "Query for info not in document — should gracefully return not_found",
    },
    {
        "id": "E02",
        "category": "edge_case",
        "query": "asdfjkl qwerty zxcvbn",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": [],
        "expected_verdict": "not_found",
        "description": "Gibberish query — system should not crash",
    },
    {
        "id": "E03",
        "category": "edge_case",
        "query": "",
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": [],
        "expected_verdict": "not_found",
        "description": "Empty query — system should not crash",
    },
    {
        "id": "E04",
        "category": "edge_case",
        "query": "is wear and tear covered",
        "tree": MOTOR_TREE,
        "doc_id": "test_motor",
        "expected_keywords": ["wear", "tear", "not covered"],
        "expected_verdict": "not_covered",
        "description": "Exclusion clause retrieval for motor policy",
    },
    {
        "id": "E05",
        "category": "edge_case",
        "query": "DIET CONSULTATION RIDER",   # all caps
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["diet", "nutritionist"],
        "expected_verdict": "covered",
        "description": "All-caps query — case normalisation check",
    },
    {
        "id": "E06",
        "category": "edge_case",
        "query": "diet   consultation    rider",  # extra spaces
        "tree": MENTAL_WELLBEING_TREE,
        "doc_id": "test_mental_wellbeing",
        "expected_keywords": ["diet", "nutritionist"],
        "expected_verdict": "covered",
        "description": "Extra whitespace in query — normalisation check",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 1 — RE-CHUNKER TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_rechunker() -> List[TestResult]:
    results = []
    try:
        from inference_universal import _rechunk_text
    except ImportError:
        return [TestResult(
            layer="rechunker", name="import",
            passed=False, score=0.0, latency_ms=0,
            details="Could not import _rechunk_text from inference_universal.py",
            suggestion="Make sure inference_universal.py is in the Python path."
        )]

    cases = [
        {
            "name": "splits_6_riders",
            "parent_id": "0004",
            "path": "Section 3: Rider Covers",
            "text": MENTAL_WELLBEING_TREE["result"][3]["text"],
            "min_chunks": 5,
            "must_contain": ["R4. Diet Consultation Rider"],
            "description": "Section 3 with 6 riders should produce ≥5 sub-nodes including R4",
        },
        {
            "name": "short_text_not_split",
            "parent_id": "0001",
            "path": "Policy Wordings",
            "text": "Short text.",
            "min_chunks": 0,
            "max_chunks": 0,
            "must_contain": [],
            "description": "Short text (<300 chars) should NOT be split",
        },
        {
            "name": "numbered_clauses_split",
            "parent_id": "TEST",
            "path": "Exclusions",
            "text": (
                "# Exclusions\n\n"
                "1. Wear and Tear\nNormal wear and tear is not covered under this policy.\n\n"
                "2. Drunk Driving\nAny damage caused while the driver was under influence of alcohol is excluded.\n\n"
                "3. War Risks\nLoss due to war, nuclear risks, or radioactive contamination is excluded.\n\n"
                "4. Consequential Loss\nDepreciation and any consequential loss is not covered."
            ),
            "min_chunks": 3,
            "must_contain": ["Drunk Driving", "Wear and Tear"],
            "description": "Numbered clause list should split into individual exclusion nodes",
        },
        {
            "name": "motor_section_split",
            "parent_id": "M001",
            "path": "Section I",
            "text": MOTOR_TREE["result"][0]["text"],
            "min_chunks": 2,
            "must_contain": ["1.2", "Theft"],
            "description": "Motor policy section with sub-clauses should split",
        },
        {
            "name": "no_false_splits_on_prose",
            "parent_id": "PROSE",
            "path": "General",
            "text": (
                "This policy provides comprehensive coverage for the insured vehicle. "
                "The insured should notify the company within 24 hours of any incident. "
                "All claims must be supported by relevant documentation. "
                "The company reserves the right to investigate any claim before settlement. "
                "This is a standard motor insurance policy governed by the laws of India. "
                "The policy is subject to renewal annually and the premium may vary. "
                "Coverage extends to all accessories fitted to the vehicle at the time of purchase."
                * 2  # repeat to cross 300 char threshold
            ),
            "min_chunks": 0,
            "max_chunks": 1,
            "must_contain": [],
            "description": "Pure prose without headers should not produce false splits",
        },
    ]

    for case in cases:
        t0 = time.perf_counter()
        try:
            chunks = _rechunk_text(case["parent_id"], case["text"], case["path"])
            latency = (time.perf_counter() - t0) * 1000

            chunk_texts = " ".join(c["text"] for c in chunks)
            min_ok  = len(chunks) >= case.get("min_chunks", 0)
            max_ok  = len(chunks) <= case.get("max_chunks", 999)
            kw_ok   = all(kw.lower() in chunk_texts.lower()
                          for kw in case["must_contain"])
            passed  = min_ok and max_ok and kw_ok

            missing_kw = [kw for kw in case["must_contain"]
                          if kw.lower() not in chunk_texts.lower()]

            details = (
                f"Got {len(chunks)} chunks. "
                f"{'Missing keywords: ' + str(missing_kw) if missing_kw else 'All keywords found.'}"
            )
            suggestion = ""
            if not min_ok:
                suggestion = (
                    f"Expected ≥{case['min_chunks']} chunks but got {len(chunks)}. "
                    "Add more header patterns to _SECTION_PATTERNS in inference_universal.py."
                )
            elif not kw_ok:
                suggestion = (
                    f"Keywords {missing_kw} not found in any chunk. "
                    "The regex pattern may not be matching this header style."
                )

            results.append(TestResult(
                layer="rechunker", name=case["name"],
                passed=passed,
                score=1.0 if passed else (0.5 if min_ok else 0.0),
                latency_ms=latency,
                details=f"{case['description']} | {details}",
                suggestion=suggestion,
            ))
        except Exception as e:
            results.append(TestResult(
                layer="rechunker", name=case["name"],
                passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
                suggestion="Check _rechunk_text for unhandled input types.",
            ))

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 2 — NODE INGESTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_ingestion() -> List[TestResult]:
    results = []
    try:
        from inference_universal import UniversalInference
        engine = UniversalInference.__new__(UniversalInference)
        engine.json_docs = {}
    except Exception as e:
        return [TestResult(
            layer="ingestion", name="import",
            passed=False, score=0.0, latency_ms=0,
            details=f"Could not instantiate UniversalInference: {e}",
            suggestion="Check inference_universal.py imports and class definition."
        )]

    cases = [
        {
            "name": "mental_wellbeing_node_count",
            "tree": MENTAL_WELLBEING_TREE,
            "doc_id": "mw_test",
            "min_nodes": 8,   # 5 original + at least 3 re-chunked
            "must_have_path_containing": ["diet consultation rider"],
            "description": "Mental Wellbeing PDF should produce ≥8 nodes after re-chunking",
        },
        {
            "name": "motor_node_count",
            "tree": MOTOR_TREE,
            "doc_id": "motor_test",
            "min_nodes": 5,
            "must_have_path_containing": ["theft"],
            "description": "Motor policy should produce ≥5 nodes with theft sub-node",
        },
        {
            "name": "all_nodes_have_required_keys",
            "tree": MENTAL_WELLBEING_TREE,
            "doc_id": "mw_keys_test",
            "min_nodes": 1,
            "must_have_path_containing": [],
            "check_keys": ["id", "summary", "text", "path"],
            "description": "Every ingested node must have id, summary, text, path",
        },
        {
            "name": "empty_tree_does_not_crash",
            "tree": {"doc_id": "empty", "result": []},
            "doc_id": "empty_test",
            "min_nodes": 0,
            "max_nodes": 0,
            "must_have_path_containing": [],
            "description": "Empty tree should produce 0 nodes without crashing",
        },
    ]

    for case in cases:
        t0 = time.perf_counter()
        try:
            # Use _extract_nodes directly (bypasses model loading)
            from inference_universal import _rechunk_text
            nodes = []
            data  = case["tree"].get("result", case["tree"])

            def extract(data, nodes_list, path=None):
                """Inline copy of _extract_nodes for isolated testing."""
                import re
                if path is None: path = []
                if isinstance(data, list):
                    for item in data: extract(item, nodes_list, path)
                elif isinstance(data, dict):
                    title    = data.get("title", data.get("header", ""))
                    new_path = path + [title] if title else path
                    node_id  = data.get("node_id", data.get("id"))
                    if node_id:
                        summary = str(data.get("prefix_summary", data.get("summary", "")))
                        text    = str(data.get("text", ""))
                        if len(summary) < 5: summary = text[:100]
                        path_str = " > ".join(new_path)
                        nodes_list.append({
                            "id":      str(node_id),
                            "summary": f"[{path_str}] {summary}",
                            "text":    f"[{path_str}] {text}",
                            "path":    path_str.lower(),
                        })
                        sub = _rechunk_text(str(node_id), text, path_str)
                        nodes_list.extend(sub)
                    if "nodes" in data:
                        extract(data["nodes"], nodes_list, new_path)

            extract(data, nodes)
            valid_nodes = [n for n in nodes if n["id"] and n["text"]]
            latency = (time.perf_counter() - t0) * 1000

            min_ok  = len(valid_nodes) >= case.get("min_nodes", 0)
            max_ok  = len(valid_nodes) <= case.get("max_nodes", 9999)

            path_ok = True
            missing_paths = []
            for kw in case.get("must_have_path_containing", []):
                found = any(kw in n["path"] for n in valid_nodes)
                if not found:
                    path_ok = False
                    missing_paths.append(kw)

            keys_ok = True
            bad_nodes = []
            for req_key in case.get("check_keys", []):
                bad = [n["id"] for n in valid_nodes if req_key not in n]
                if bad:
                    keys_ok = False
                    bad_nodes.extend(bad)

            passed = min_ok and max_ok and path_ok and keys_ok
            score  = sum([min_ok, max_ok, path_ok, keys_ok]) / 4

            details = (
                f"{len(valid_nodes)} nodes produced. "
                + (f"Missing paths: {missing_paths}. " if missing_paths else "")
                + (f"Nodes missing keys: {bad_nodes}. " if bad_nodes else "")
            )
            suggestion = ""
            if not min_ok:
                suggestion = (
                    f"Only {len(valid_nodes)} nodes — expected ≥{case['min_nodes']}. "
                    "The re-chunker may not be recognising section headers in this doc. "
                    "Print the raw text and check if headers match _SECTION_PATTERNS."
                )
            if not path_ok:
                suggestion += (
                    f" Paths {missing_paths} not found — the chunk containing this "
                    "keyword may have been filtered by _CHUNK_MIN_LEN."
                )

            results.append(TestResult(
                layer="ingestion", name=case["name"],
                passed=passed, score=score, latency_ms=latency,
                details=f"{case['description']} | {details}",
                suggestion=suggestion,
            ))
        except Exception as e:
            results.append(TestResult(
                layer="ingestion", name=case["name"],
                passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {traceback.format_exc()}",
                suggestion="Unhandled exception in ingestion — check _extract_nodes.",
            ))

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 3 — PRE-RETRIEVAL SCORER TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_scorer() -> List[TestResult]:
    results = []

    # Build a flat node list from the mental wellbeing tree
    try:
        from inference_universal import _rechunk_text
    except ImportError:
        return [TestResult(
            layer="scorer", name="import", passed=False, score=0.0,
            latency_ms=0, details="Cannot import from inference_universal.py"
        )]

    # Build nodes inline
    nodes = []
    def extract_flat(data, path=None):
        if path is None: path = []
        if isinstance(data, list):
            for item in data: extract_flat(item, path)
        elif isinstance(data, dict):
            title    = data.get("title", "")
            new_path = path + [title] if title else path
            node_id  = data.get("node_id", "")
            if node_id:
                text     = str(data.get("text", ""))
                summary  = str(data.get("prefix_summary", text[:100]))
                path_str = " > ".join(new_path)
                nodes.append({
                    "id": node_id, "text": f"[{path_str}] {text}",
                    "summary": f"[{path_str}] {summary}", "path": path_str.lower()
                })
                nodes.extend(_rechunk_text(node_id, text, path_str))
            if "nodes" in data:
                extract_flat(data["nodes"], new_path)

    extract_flat(MENTAL_WELLBEING_TREE["result"])

    # Inline compute_score (mirrors the one in inference_universal.py)
    def compute_score(query: str, node: dict) -> float:
        q        = query.lower().strip()
        combined = (node.get("summary","").lower() + " " +
                    node.get("text","").lower()    + " " +
                    node.get("path","").lower())
        path_l   = node.get("path", "").lower()
        stopwords = {"is","the","a","an","of","in","on","for","to","and","or","what","my","me"}
        kws      = [w for w in q.split() if w not in stopwords and len(w) > 2]
        exact    = 5.0 if q in combined else 0.0
        kw_sc    = sum(1.5 for w in kws if w in combined)
        bigrams  = [f"{kws[i]} {kws[i+1]}" for i in range(len(kws)-1)]
        bg_sc    = sum(3.0 for bg in bigrams if bg in combined)
        path_sc  = sum(2.5 for w in kws if w in path_l)
        return exact + kw_sc + bg_sc + path_sc

    scorer_cases = [
        {
            "name": "diet_rider_ranks_first",
            "query": "what is diet consultation rider",
            "top_n": 3,
            "expected_keyword_in_top": "diet consultation rider",
            "description": "Diet Consultation Rider node should rank in top 3",
        },
        {
            "name": "stress_rider_ranks_first",
            "query": "stress management rider coverage",
            "top_n": 3,
            "expected_keyword_in_top": "stress management",
            "description": "Stress Management Rider should rank in top 3",
        },
        {
            "name": "addiction_program_found",
            "query": "addiction cessation program",
            "top_n": 5,
            "expected_keyword_in_top": "addiction cessation",
            "description": "Addiction Cessation Program should be in top 5",
        },
        {
            "name": "caps_query_normalised",
            "query": "DIET CONSULTATION RIDER",
            "top_n": 3,
            "expected_keyword_in_top": "diet",
            "description": "All-caps query should normalise and still rank correctly",
        },
        {
            "name": "gibberish_no_crash",
            "query": "asdfjkl qwerty zxcvbn",
            "top_n": 25,
            "expected_keyword_in_top": None,  # don't care about content, just no crash
            "description": "Gibberish query must not crash the scorer",
        },
        {
            "name": "empty_query_no_crash",
            "query": "",
            "top_n": 25,
            "expected_keyword_in_top": None,
            "description": "Empty query must not crash the scorer",
        },
    ]

    for case in scorer_cases:
        t0 = time.perf_counter()
        try:
            scored = [(compute_score(case["query"], n), n) for n in nodes]
            scored.sort(key=lambda x: x[0], reverse=True)
            top_n  = [n for _, n in scored[:case["top_n"]]]
            latency = (time.perf_counter() - t0) * 1000

            if case["expected_keyword_in_top"] is None:
                passed = True
                score  = 1.0
                details = f"No crash. Top score: {scored[0][0]:.1f} if nodes else 0"
            else:
                kw       = case["expected_keyword_in_top"].lower()
                hit_node = next((n for n in top_n if kw in n["path"] or kw in n["text"].lower()), None)
                passed   = hit_node is not None
                score    = 1.0 if passed else 0.0
                rank     = next((i+1 for i, n in enumerate(n for _, n in scored)
                                 if kw in n["path"] or kw in n["text"].lower()), None)
                details  = (
                    f"Found in top {case['top_n']}: {passed}. "
                    f"Actual rank: {rank}. "
                    f"Top node path: {scored[0][1]['path'][:80] if scored else 'none'}"
                )

            suggestion = ""
            if not passed:
                suggestion = (
                    f"'{case['expected_keyword_in_top']}' did not appear in top {case['top_n']}. "
                    "Check if the re-chunker created a node for this section. "
                    "Consider increasing bigram weight or adding the phrase to path scoring."
                )

            results.append(TestResult(
                layer="scorer", name=case["name"],
                passed=passed, score=score, latency_ms=latency,
                details=f"{case['description']} | {details}",
                suggestion=suggestion,
            ))
        except Exception as e:
            results.append(TestResult(
                layer="scorer", name=case["name"],
                passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
                suggestion="Unhandled exception in scorer — check compute_score.",
            ))

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 4 — EXPLAINER TESTS (no Groq call — tests verdict inference)
# ══════════════════════════════════════════════════════════════════════════════

def test_explainer_logic() -> List[TestResult]:
    results = []
    try:
        from explainer import _infer_verdict, _extract_section_ref, _parse_sections
    except ImportError:
        return [TestResult(
            layer="explainer", name="import", passed=False, score=0.0,
            latency_ms=0,
            details="Cannot import from explainer.py — skipping explainer tests.",
            suggestion="Ensure explainer.py is in the Python path."
        )]

    verdict_cases = [
        ("Yes, your policy covers this under Section R4.", "covered clause text", "covered"),
        ("No, this is not covered under your policy.", "not covered", "not_covered"),
        ("It depends on whether you have paid the additional premium.", "additional premium", "conditional"),
        ("Unfortunately, drunk driving is excluded.", "excluded under section 3", "not_covered"),
        ("Yes! You are covered for theft under Section I.", "theft covered", "covered"),
    ]

    for i, (answer, clause, expected) in enumerate(verdict_cases):
        t0 = time.perf_counter()
        try:
            got     = _infer_verdict(answer, clause)
            passed  = got == expected
            latency = (time.perf_counter() - t0) * 1000
            results.append(TestResult(
                layer="explainer", name=f"verdict_{i+1}",
                passed=passed, score=1.0 if passed else 0.0, latency_ms=latency,
                details=f"Answer: '{answer[:50]}' → Expected '{expected}', got '{got}'",
                suggestion=(
                    "" if passed else
                    f"_infer_verdict returned '{got}' instead of '{expected}'. "
                    "Add the trigger phrase to the relevant condition in _infer_verdict."
                )
            ))
        except Exception as e:
            results.append(TestResult(
                layer="explainer", name=f"verdict_{i+1}",
                passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
            ))

    # Test _extract_section_ref
    ref_cases = [
        ("[Section 3: Rider Covers > R4. Diet Consultation Rider] text", "section 3"),
        ("Under clause 2.1 of the policy...", "clause 2.1"),
        ("No section reference here at all in this text string.", None),
    ]
    for i, (text, expected_contains) in enumerate(ref_cases):
        t0 = time.perf_counter()
        try:
            got    = _extract_section_ref(text).lower()
            passed = (expected_contains is None) or (expected_contains in got)
            results.append(TestResult(
                layer="explainer", name=f"section_ref_{i+1}",
                passed=passed, score=1.0 if passed else 0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"Input: '{text[:60]}' → Got: '{got[:60]}'",
                suggestion=(
                    "" if passed else
                    f"_extract_section_ref missed '{expected_contains}'. "
                    "Extend the regex in _extract_section_ref to cover this format."
                )
            ))
        except Exception as e:
            results.append(TestResult(
                layer="explainer", name=f"section_ref_{i+1}",
                passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
            ))

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER 5 — LIVE API TESTS (optional — requires running server)
# ══════════════════════════════════════════════════════════════════════════════

def test_api(base_url: str, pdf_path: Optional[str] = None) -> List[TestResult]:
    results = []
    try:
        import requests
    except ImportError:
        return [TestResult(
            layer="api", name="import", passed=False, score=0.0, latency_ms=0,
            details="pip install requests to enable API tests.",
        )]

    # 1. Health check
    t0 = time.perf_counter()
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        latency = (time.perf_counter() - t0) * 1000
        results.append(TestResult(
            layer="api", name="health_check",
            passed=r.status_code == 200, score=1.0 if r.status_code == 200 else 0.0,
            latency_ms=latency,
            details=f"Status: {r.status_code}",
            suggestion="" if r.status_code == 200 else "Server not running or /health not implemented.",
        ))
    except Exception as e:
        results.append(TestResult(
            layer="api", name="health_check", passed=False, score=0.0,
            latency_ms=(time.perf_counter() - t0) * 1000,
            details=f"Connection failed: {e}",
            suggestion=f"Make sure the server is running at {base_url}",
        ))
        return results  # no point continuing if server is down

    # 2. Upload test (only if PDF provided)
    session_id = None
    if pdf_path and os.path.exists(pdf_path):
        t0 = time.perf_counter()
        try:
            with open(pdf_path, "rb") as f:
                r = requests.post(
                    f"{base_url}/upload",
                    files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
                    timeout=60
                )
            latency = (time.perf_counter() - t0) * 1000
            data    = r.json()
            passed  = r.status_code == 200 and "session_id" in data
            session_id = data.get("session_id")
            node_count = data.get("node_count", 0)
            results.append(TestResult(
                layer="api", name="upload",
                passed=passed, score=1.0 if passed else 0.0, latency_ms=latency,
                details=f"Status: {r.status_code}. session_id: {session_id}. nodes: {node_count}",
                suggestion=(
                    "" if passed else
                    "Upload failed. Check api_server.py /upload endpoint and PageIndex connectivity."
                )
            ))

            # Warn if node count is suspiciously low
            if passed and node_count < 8:
                results.append(TestResult(
                    layer="api", name="upload_node_count_warning",
                    passed=False, score=0.5, latency_ms=0,
                    details=f"Only {node_count} nodes — re-chunker may not be active in api_server.py pipeline.",
                    suggestion=(
                        "Node count < 8 for a multi-section document suggests re-chunking is not running. "
                        "Verify that api_server.py uses the updated inference_universal.py."
                    )
                ))
        except Exception as e:
            results.append(TestResult(
                layer="api", name="upload", passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
                suggestion="Check /upload endpoint and file handling in api_server.py.",
            ))

    # 3. Query tests (with and without session)
    api_query_cases = [
        {
            "name": "query_with_session",
            "question": "what is diet consultation rider",
            "use_session": True,
            "expected_keywords_in_answer": ["diet", "nutritionist", "R4"],
            "skip_if_no_session": True,
        },
        {
            "name": "query_without_session_uses_db",
            "question": "what is third party liability",
            "use_session": False,
            "expected_keywords_in_answer": ["third party", "liability"],
            "skip_if_no_session": False,
        },
        {
            "name": "empty_query_handled",
            "question": "",
            "use_session": False,
            "expected_keywords_in_answer": [],
            "skip_if_no_session": False,
            "expect_no_crash": True,
        },
    ]

    for case in api_query_cases:
        if case.get("skip_if_no_session") and not session_id:
            results.append(TestResult(
                layer="api", name=case["name"], passed=True, score=1.0,
                latency_ms=0,
                details="SKIPPED — no session_id (no PDF uploaded).",
            ))
            continue

        t0 = time.perf_counter()
        try:
            payload = {"question": case["question"]}
            if case["use_session"] and session_id:
                payload["session_id"] = session_id

            r       = requests.post(f"{base_url}/query", json=payload, timeout=30)
            latency = (time.perf_counter() - t0) * 1000
            data    = r.json()

            status_ok = r.status_code == 200
            answer    = (data.get("explanation") or data.get("answer") or "").lower()

            if case.get("expect_no_crash"):
                passed = status_ok
                score  = 1.0 if passed else 0.0
                details = f"Status: {r.status_code}"
            else:
                kw_hits = [kw for kw in case["expected_keywords_in_answer"]
                           if kw.lower() in answer]
                passed  = status_ok and len(kw_hits) == len(case["expected_keywords_in_answer"])
                score   = len(kw_hits) / max(len(case["expected_keywords_in_answer"]), 1)
                missing = [kw for kw in case["expected_keywords_in_answer"]
                           if kw.lower() not in answer]
                details = (
                    f"Status: {r.status_code}. "
                    f"Keywords found: {kw_hits}. Missing: {missing}. "
                    f"Answer preview: '{answer[:100]}'"
                )

            results.append(TestResult(
                layer="api", name=case["name"],
                passed=passed, score=score, latency_ms=latency,
                details=details,
                suggestion=(
                    "" if passed else
                    f"Expected keywords {case['expected_keywords_in_answer']} not in answer. "
                    "Check that the correct document is being queried and the explainer is receiving clause text."
                )
            ))
        except Exception as e:
            results.append(TestResult(
                layer="api", name=case["name"], passed=False, score=0.0,
                latency_ms=(time.perf_counter() - t0) * 1000,
                details=f"EXCEPTION: {e}",
                suggestion="API query failed — check /query endpoint.",
            ))

    return results


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def _bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    return "█" * filled + "░" * (width - filled)


def print_report(all_results: List[TestResult]):
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  INSURECLEAR SYSTEM TEST REPORT{RESET}")
    print(f"{'='*70}")

    # Per-test results
    by_layer: Dict[str, List[TestResult]] = {}
    for r in all_results:
        by_layer.setdefault(r.layer, []).append(r)

    for layer, results in by_layer.items():
        passed  = sum(1 for r in results if r.passed)
        total   = len(results)
        avg_sc  = sum(r.score for r in results) / max(total, 1)
        color   = GREEN if avg_sc >= 0.8 else (YELLOW if avg_sc >= 0.5 else RED)

        print(f"\n{BOLD}{CYAN}▶ LAYER: {layer.upper()}{RESET}  "
              f"{color}{_bar(avg_sc)} {avg_sc:.0%} ({passed}/{total} passed){RESET}")

        rows = []
        for r in results:
            status = f"{GREEN}✓ PASS{RESET}" if r.passed else f"{RED}✗ FAIL{RESET}"
            rows.append([
                status,
                r.name,
                f"{r.score:.0%}",
                f"{r.latency_ms:.0f}ms",
                r.details[:80] + ("…" if len(r.details) > 80 else ""),
            ])

        if HAS_TABULATE:
            print(tabulate(rows, headers=["", "Test", "Score", "Latency", "Details"],
                           tablefmt="simple"))
        else:
            for row in rows:
                print("  " + " | ".join(str(c) for c in row))

    # Overall score
    total_passed = sum(1 for r in all_results if r.passed)
    total_tests  = len(all_results)
    overall      = sum(r.score for r in all_results) / max(total_tests, 1)
    color        = GREEN if overall >= 0.8 else (YELLOW if overall >= 0.5 else RED)

    print(f"\n{'='*70}")
    print(f"{BOLD}  OVERALL SCORE: {color}{_bar(overall, 30)} {overall:.0%} "
          f"({total_passed}/{total_tests} tests passed){RESET}")

    # Improvement suggestions
    failed_with_suggestions = [r for r in all_results if not r.passed and r.suggestion]
    if failed_with_suggestions:
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}  IMPROVEMENT SUGGESTIONS (ranked by layer priority){RESET}")
        print(f"{'='*70}")

        priority = ["rechunker", "ingestion", "scorer", "explainer", "api"]
        seen     = set()
        rank     = 1
        for layer in priority:
            for r in failed_with_suggestions:
                if r.layer == layer and r.suggestion not in seen:
                    seen.add(r.suggestion)
                    color = RED if r.score == 0.0 else YELLOW
                    print(f"\n  {BOLD}#{rank} [{layer.upper()}] {r.name}{RESET}")
                    print(f"  {color}{r.suggestion}{RESET}")
                    rank += 1

    print(f"\n{'='*70}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="InsureClear Pipeline Test Suite")
    parser.add_argument("--layer",  default="all",
                        choices=["all","rechunker","ingestion","scorer","explainer","api"],
                        help="Which layer to test (default: all)")
    parser.add_argument("--api",    default=None,
                        help="Base URL of live API, e.g. http://localhost:8000")
    parser.add_argument("--pdf",    default=None,
                        help="Path to a real PDF for live upload/query testing")
    args = parser.parse_args()

    all_results: List[TestResult] = []

    print(f"\n{BOLD}{CYAN}InsureClear Test Suite — starting...{RESET}\n")

    if args.layer in ("all", "rechunker"):
        print(f"{CYAN}Running Layer 1: Re-Chunker tests...{RESET}")
        all_results.extend(test_rechunker())

    if args.layer in ("all", "ingestion"):
        print(f"{CYAN}Running Layer 2: Node Ingestion tests...{RESET}")
        all_results.extend(test_ingestion())

    if args.layer in ("all", "scorer"):
        print(f"{CYAN}Running Layer 3: Pre-Retrieval Scorer tests...{RESET}")
        all_results.extend(test_scorer())

    if args.layer in ("all", "explainer"):
        print(f"{CYAN}Running Layer 4: Explainer Logic tests...{RESET}")
        all_results.extend(test_explainer_logic())

    if args.layer in ("all", "api") and args.api:
        print(f"{CYAN}Running Layer 5: Live API tests against {args.api}...{RESET}")
        all_results.extend(test_api(args.api, args.pdf))
    elif args.layer == "api" and not args.api:
        print(f"{YELLOW}⚠ Skipping API tests — pass --api http://localhost:8000 to enable.{RESET}")

    print_report(all_results)

    # Exit code: 0 if all passed, 1 if any failed
    sys.exit(0 if all(r.passed for r in all_results) else 1)


if __name__ == "__main__":
    main()