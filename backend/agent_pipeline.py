from dotenv import load_dotenv

# Ensure environment variables are loaded immediately for all modules
load_dotenv()

import os
import json
import time
import re
import operator
import sys
from typing import TypedDict, Annotated, List, Dict, Any, Optional

from google import genai
from google.genai import types
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pageindex import PageIndexClient
from inference_universal import UniversalInference
from explainer import explain_query_answer

# ==========================================
# ⚙️ 1. SETUP & CONFIGURATION
# ==========================================
gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
pageindex_key = os.environ.get("PAGEINDEX_API_KEY", "").strip()

if not gemini_key or not pageindex_key:
    raise ValueError("❌ Missing API Keys in .env file.")

client = genai.Client(api_key=gemini_key)
pi_client = PageIndexClient(api_key=pageindex_key)

# ---------------------------------------------------------------------------
# 🧠 Universal Selector — loaded once at startup
# ---------------------------------------------------------------------------
universal_selector = UniversalInference(
    model_path="./universal_selector",
    data_folder="./data/",
)

# Map of domain names to their pre-processed JSON filenames in ./data/
DOMAIN_DOC_MAP = {
    "LIFE":       "HDFC-Life-Click-2-Protect-Life-101N139V04-Policy-Document_tree",
    "HEALTH":     "new-complete-health-insurance-brochure_tree",
    "MOTOR":      "BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree",
    "PROPERTY":   "tata_aig_home_protect_plus_policy_policy_wordings_190cb1709a_tree",
    "TRAVEL":     "BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree",
    "COMMERCIAL": "BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree",
    "UNKNOWN":    "brochure-eng1_tree",
}

# ✅ FIX: Add thread_id to AgentState so nodes can look up the session store
class AgentState(TypedDict):
    messages:          Annotated[List[dict], operator.add]
    thread_id:         str                   # ← NEW: carried through every turn
    current_domain:    str
    refined_question:  str
    is_comparison:     bool
    rl_output:         Dict[str, Any]
    final_explanation: str
    # temp_policy_tree intentionally REMOVED from LangGraph state —
    # it now lives exclusively in _session_store to avoid loss between turns.

# ==========================================
# 🗂️ SESSION STORE — fixes the core bug
# ==========================================
# LangGraph's MemorySaver checkpoints state between graph runs, but
# partial invocations (passing only "messages") can cause non-reduced
# keys like temp_policy_tree to be unreliable across turns.
#
# Solution: maintain a plain Python dict keyed by thread_id as the
# single source of truth for the uploaded tree. The graph nodes read
# from here directly, so the tree is NEVER lost between turns.
_session_store: Dict[str, Dict[str, Any]] = {}

def get_session(thread_id: str) -> Dict[str, Any]:
    if thread_id not in _session_store:
        _session_store[thread_id] = {"temp_policy_tree": None}
    return _session_store[thread_id]

def set_temp_tree(thread_id: str, tree: Dict[str, Any]):
    get_session(thread_id)["temp_policy_tree"] = tree

def get_temp_tree(thread_id: str) -> Optional[Dict[str, Any]]:
    return get_session(thread_id).get("temp_policy_tree")

def clear_temp_tree(thread_id: str):
    get_session(thread_id)["temp_policy_tree"] = None


# ==========================================
# 🧹 TEMPORARY FILE PROCESSOR
# ==========================================
def clean_json_tree(tree_data):
    """Strips image tags so they don't bloat the temporary chat memory."""
    if not tree_data or "result" not in tree_data or "nodes" not in tree_data["result"]:
        return tree_data
    img_pattern = re.compile(r'!\[.*?\]\(.*?\)')
    for node in tree_data["result"]["nodes"]:
        if "text" in node and node["text"]:
            node["text"] = img_pattern.sub('', node["text"])
        if "summary" in node and node["summary"]:
            node["summary"] = img_pattern.sub('', node["summary"])
    return tree_data

def process_temp_pdf(pdf_path):
    """Uploads to PageIndex, returns JSON dict, and DOES NOT save to disk."""
    print(f"\n   ⏳ [Secure Memory] Processing '{os.path.basename(pdf_path)}'...")
    try:
        submission = pi_client.submit_document(pdf_path)
        doc_id = submission["doc_id"]

        while not pi_client.is_retrieval_ready(doc_id):
            time.sleep(3)

        raw_tree = pi_client.get_tree(doc_id, node_summary=True)
        print(f"   ✅ [Secure Memory] PDF converted to Vectorless JSON successfully.")
        return clean_json_tree(raw_tree)
    except Exception as e:
        print(f"   ❌ Upload Error: {e}")
        return None


# ==========================================
# 🧠 2. DEFINE THE NODES
# ==========================================

def router_node(state: AgentState) -> AgentState:
    user_query = state["messages"][-1]["content"]
    thread_id  = state.get("thread_id", "default")

    # ✅ FIX: Read temp tree from session store, not from LangGraph state
    has_temp_file = get_temp_tree(thread_id) is not None

    prompt = f"""
    You are an expert Insurance RAG Pre-processor.
    User Query: "{user_query}"
    Context: {"The user has an uploaded custom policy active." if has_temp_file else "No custom policy uploaded."}

    Task 1: Categorize into: [LIFE, HEALTH, MOTOR, PROPERTY, TRAVEL, COMMERCIAL, UNKNOWN].
    Task 2: Rewrite into a highly detailed, formal question for an RL extraction model.
    Task 3: If the user is asking to compare two policies, contrast them, or find differences, set 'is_comparison' to true. Otherwise, false.

    Return ONLY JSON:
    {{"domain": "CATEGORY", "refined_question": "...", "is_comparison": true/false}}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        result = json.loads(response.text)
        return {
            "current_domain":    result.get("domain", "UNKNOWN"),
            "refined_question":  result.get("refined_question", user_query),
            "is_comparison":     result.get("is_comparison", False),  # ✅ FIX: was missing
        }
    except:
        return {
            "current_domain":   "UNKNOWN",
            "refined_question": user_query,
            "is_comparison":    False,
        }


def rl_extraction_node(state: AgentState) -> AgentState:
    refined_q  = state["refined_question"]
    domain     = state["current_domain"]
    is_compare = state.get("is_comparison", False)
    thread_id  = state.get("thread_id", "default")

    # ✅ FIX: Always pull temp tree from session store — never from LangGraph state.
    # This guarantees the tree survives across multiple query turns.
    temp_tree = get_temp_tree(thread_id)
    has_temp  = temp_tree is not None

    targets = []

    # 🟢 SCENARIO A: COMPARISON MODE — uploaded policy vs database document
    if is_compare and has_temp:
        print(f"   [RL System] COMPARISON MODE for: '{refined_q}'")
        targets.append({"doc_id": "User_Uploaded_Policy", "tree": temp_tree})
        db_doc_id = DOMAIN_DOC_MAP.get(domain, DOMAIN_DOC_MAP["UNKNOWN"])
        targets.append(db_doc_id)

    # 🔵 SCENARIO B: UPLOAD PRESENT — query against uploaded doc only
    elif has_temp:
        print("   [RL System] Querying Uploaded Policy...")
        targets.append({"doc_id": "User_Uploaded_Policy", "tree": temp_tree})

    # 🟣 SCENARIO C: NO UPLOAD — query the permanent database
    else:
        print("   [RL System] Querying Permanent Database...")
        db_doc_id = DOMAIN_DOC_MAP.get(domain, DOMAIN_DOC_MAP["UNKNOWN"])
        targets.append(db_doc_id)

    rl_response = universal_selector.extract_payload(refined_q, targets)
    return {"rl_output": rl_response}


def explainer_node(state: AgentState) -> AgentState:
    """
    Final node in the graph. 
    1. Grabs the raw RL output (selected clauses).
    2. Passes it to the Groq-powered explainer.py for a plain-English reply.
    """
    user_query = state["messages"][-1]["content"]
    rl_data    = state["rl_output"]

    # Ensure the explainer knows what the original question was
    rl_data["user_question"] = user_query

    # Call the production explainer layer
    explanation_result = explain_query_answer(rl_data)
    
    # Extract the primary answer for the chat message
    final_text = explanation_result.get("answer", "No relevant clauses found.")

    return {
        "final_explanation": final_text,
        "messages": [{"role": "assistant", "content": final_text}]
    }


# ==========================================
# 🕸️ 3. BUILD AND COMPILE THE GRAPH
# ==========================================

# ✅ FIX: Add thread_id to AgentState so nodes can look up the session store
# Moved up to top of file

workflow = StateGraph(AgentState)
workflow.add_node("router",      router_node)
workflow.add_node("rl_extractor", rl_extraction_node)
workflow.add_node("explainer",   explainer_node)

workflow.add_edge(START,         "router")
workflow.add_edge("router",      "rl_extractor")
workflow.add_edge("rl_extractor","explainer")
workflow.add_edge("explainer",   END)

memory = MemorySaver()
app    = workflow.compile(checkpointer=memory)


# ==========================================
# 🚀 4. INTERACTIVE CHAT LOOP
# ==========================================
def run_chat():
    print("=" * 60)
    print("🤖 Production Agentic Bot Online! (Supports Memory & Temporary Uploads)")
    print("Commands:")
    print("  - Type a question to chat.")
    print("  - Type '/upload filepath.pdf' to upload a temporary policy.")
    print("  - Type '/clear' to remove the uploaded policy.")
    print("  - Type 'exit' to quit.\n")

    THREAD_ID = "secure_session_001"
    config    = {"configurable": {"thread_id": THREAD_ID}}

    while True:
        user_input = input("👤 You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break

        # 🟢 HANDLE DYNAMIC FILE UPLOADS
        if user_input.startswith("/upload"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                print("   ⚠️  Please provide a file path. Example: /upload my_policy.pdf")
                continue

            pdf_path = parts[1].strip()
            if not os.path.exists(pdf_path):
                print(f"   ⚠️  File not found: {pdf_path}")
                continue

            temp_tree = process_temp_pdf(pdf_path)
            if temp_tree:
                # ✅ FIX: Store tree in session store, NOT in initial_state.
                # This way every subsequent query in the same session finds it.
                set_temp_tree(THREAD_ID, temp_tree)

                initial_state = {
                    "thread_id": THREAD_ID,
                    "messages":  [{"role": "user", "content": "I just uploaded a custom policy. Can you explain the main coverages?"}]
                }
                print("   ⏳ Generating explanation for uploaded policy...")
                result = app.invoke(initial_state, config=config)
                print(f"\n🤖 System: {result['final_explanation']}")
                print("-" * 60)
            continue

        # 🔴 CLEAR uploaded policy
        if user_input.lower() == "/clear":
            clear_temp_tree(THREAD_ID)
            print("   ✅ Uploaded policy cleared. Now querying permanent database.")
            continue

        # ✅ FIX: Always include thread_id so nodes can reach the session store.
        # No temp_policy_tree here — it lives in _session_store.
        print("   ⏳ Thinking...")
        initial_state = {
            "thread_id": THREAD_ID,
            "messages":  [{"role": "user", "content": user_input}]
        }
        result = app.invoke(initial_state, config=config)

        print(f"\n🤖 System: {result['final_explanation']}")
        print("-" * 60)


if __name__ == "__main__":
    run_chat()