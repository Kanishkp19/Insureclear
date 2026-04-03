import os
import json
import time
import re
import operator
import sys
from typing import TypedDict, Annotated, List, Dict, Any
from dotenv import load_dotenv

from google import genai
from google.genai import types
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from pageindex import PageIndexClient

# ==========================================
# ⚙️ 1. SETUP & CONFIGURATION
# ==========================================
load_dotenv()
gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
pageindex_key = os.environ.get("PAGEINDEX_API_KEY", "").strip()

if not gemini_key or not pageindex_key:
    raise ValueError("❌ Missing API Keys in .env file.")

client = genai.Client(api_key=gemini_key)
pi_client = PageIndexClient(api_key=pageindex_key)

# Define the LangGraph State
class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add] 
    current_domain: str
    refined_question: str
    temp_policy_tree: Dict[str, Any]  
    is_comparison: bool               # 🟢 NEW: Flag for comparison mode
    rl_output: Dict[str, Any]
    final_explanation: str

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
    current_domain = state.get("current_domain", "UNKNOWN")
    has_temp_file = "temp_policy_tree" in state and state["temp_policy_tree"] is not None
    
    # Let the Router know if a temporary file is active
    context_hint = "The user has uploaded a custom policy." if has_temp_file else ""
    
    prompt = f"""
    You are an expert Insurance RAG Pre-processor.
    User Query: "{user_query}"
    
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
        return {"current_domain": result.get("domain", "UNKNOWN"), 
                "refined_question": result.get("refined_question", user_query)}
    except:
        return {"current_domain": "UNKNOWN", "refined_question": user_query}


def rl_extraction_node(state: AgentState) -> AgentState:
    refined_q = state["refined_question"]
    domain = state["current_domain"]
    is_compare = state.get("is_comparison", False)
    has_temp = state.get("temp_policy_tree") is not None
    
    real_rl_response = {"user_question": refined_q, "selected_clauses": []}
    
    # 🟢 SCENARIO A: COMPARISON MODE
    if is_compare and has_temp:
        print(f"   [RL System] COMPARISON MODE INITIATED for: '{refined_q}'")
        
        # 1. Extract from the Uploaded Policy
        # temp_result = your_rl_model.run(refined_q, state["temp_policy_tree"])
        
        # 2. Extract from the Permanent Database (based on domain)
        # db_result = your_rl_model.run(refined_q, f"Database_{domain}")
        
        

    # 🔵 SCENARIO B: NORMAL UPLOAD QUERY (No comparison)
    elif has_temp:
        print("   [RL System] Searching Uploaded Policy...")
        real_rl_response["selected_clauses"].append({
            "document_id": "User_Uploaded_Temp_Policy", "confidence_score": 0.95, "text": "..."
        })
        
    # 🟣 SCENARIO C: NORMAL DATABASE QUERY
    else:
        print("   [RL System] Searching Permanent Database...")
        real_rl_response["selected_clauses"].append({
            "document_id": f"Database_{domain}", "confidence_score": 0.95, "text": "..."
        })
        
    return {"rl_output": real_rl_response}


def explainer_node(state: AgentState) -> AgentState:
    user_query = state["messages"][-1]["content"]
    rl_data = state["rl_output"]
    is_compare = state.get("is_comparison", False)
    
    # Format all high-confidence clauses found by the RL model
    extracted_text_block = ""
    for clause in rl_data.get("selected_clauses", []):
        if clause.get("confidence_score", 0) > 0.50:
            extracted_text_block += f"\n- Source [{clause['document_id']}]: {clause['text']}"
            
    if not extracted_text_block:
        extracted_text_block = "No relevant clauses found in the provided documents."

    prompt = f"""
    You are an expert Insurance Analyst.
    
    User's Original Question: "{user_query}"
    Clauses Extracted by System: 
    {extracted_text_block}
    
    Task: 
    1. If there are multiple sources listed, clearly COMPARE them. Tell the user what their uploaded policy says versus what our database policy says. Highlight which one is better for the user's specific question.
    2. If there is only one source, simply explain the rule clearly and empathetically.
    3. DO NOT invent rules. Base your answer strictly on the extracted text provided above.
    """
    
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    explanation = response.text.strip()
    
    return {
        "final_explanation": explanation,
        "messages": [{"role": "assistant", "content": explanation}]
    }

# ==========================================
# 🕸️ 3. BUILD AND COMPILE THE GRAPH
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.add_node("rl_extractor", rl_extraction_node)
workflow.add_node("explainer", explainer_node)

workflow.add_edge(START, "router")
workflow.add_edge("router", "rl_extractor")
workflow.add_edge("rl_extractor", "explainer")
workflow.add_edge("explainer", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ==========================================
# 🚀 4. INTERACTIVE CHAT LOOP
# ==========================================
def run_chat():
    print("="*60)
    print("🤖 Production Agentic Bot Online! (Supports Memory & Temporary Uploads)")
    print("Commands:")
    print("  - Type a question to chat.")
    print("  - Type '/upload filepath.pdf' to upload a temporary policy.")
    print("  - Type 'exit' to quit.\n")
    
    config = {"configurable": {"thread_id": "secure_session_001"}}
    
    while True:
        user_input = input("👤 You: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # 🟢 HANDLE DYNAMIC FILE UPLOADS
        if user_input.startswith("/upload"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2:
                print("   ⚠️ Please provide a file path. Example: /upload my_policy.pdf")
                continue
                
            pdf_path = parts[1].strip()
            if not os.path.exists(pdf_path):
                print(f"   ⚠️ File not found: {pdf_path}")
                continue
                
            # Process to JSON dictionary in-memory
            temp_tree = process_temp_pdf(pdf_path)
            
            if temp_tree:
                # We inject the JSON tree directly into the state memory!
                # We also add a message so the LLM knows the user uploaded it.
                initial_state = {
                    "temp_policy_tree": temp_tree,
                    "messages": [{"role": "user", "content": "I just uploaded a custom policy. Can you explain the main coverages?"}]
                }
                print("   ⏳ Generating explanation for uploaded policy...")
                result = app.invoke(initial_state, config=config)
                print(f"\n🤖 System: {result['final_explanation']}")
                print("-" * 60)
            continue
            
        # Standard Chat Flow
        print("   ⏳ Thinking...")
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        result = app.invoke(initial_state, config=config)
        
        print(f"\n🤖 System: {result['final_explanation']}")
        print("-" * 60)

if __name__ == "__main__":
    run_chat()