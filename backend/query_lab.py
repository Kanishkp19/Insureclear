import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load the Gemini API Key from your .env file
load_dotenv()
gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

if not gemini_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file.")

# 2. Initialize the Gemini Client
client = genai.Client(api_key=gemini_key)

def preprocess_query(user_query, current_ui_selection="None"):
    """
    Takes a raw user query, categorizes the domain, and expands it into 
    a highly detailed, formal question for the RL extraction model.
    """
    prompt = f"""
    You are an expert Insurance QA Pre-processor.
    
    User Query: "{user_query}"
    User's Current UI Selection (if any): {current_ui_selection}
    
    Task 1: Categorize the query into one of: [LIFE, HEALTH, MOTOR, PROPERTY, TRAVEL, COMMERCIAL, UNKNOWN].
    Task 2: Rewrite the user's query into a highly detailed, formal QUESTION. Enhance it by weaving in relevant insurance terminology, synonyms, and specific conditions (e.g., 'acts of god', 'waiting periods', 'exclusions', 'third-party'). It MUST remain a natural language question so a downstream QA model can process it.
    
    Return ONLY a JSON object in this exact format:
    {{
      "domain": "CATEGORY",
      "refined_question": "Does the property insurance policy cover structural damage to the roof caused by falling objects, such as a tree, during a hurricane or natural disaster?"
    }}
    """
    
    try:
        # Using Gemini 2.5 Flash for lightning-fast reasoning
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", # Forces strict JSON output
            )
        )
        
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"\n❌ Error during preprocessing: {e}")
        return {"domain": "UNKNOWN", "refined_question": user_query}


# ==========================================
# AUTOMATED TESTS & INTERACTIVE LAB
# ==========================================
def run_tests():
    print("🚀 Running Automated RAG Preprocessing Tests...\n")
    
    test_queries = [
        "A tree fell on my roof during the hurricane.",
        "I got bit by a dog and need rabies shots, will they pay?",
        "Someone keyed my car door in the parking lot."
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"--- Test Case {i} ---")
        print(f"👤 Raw Query:   {query}")
        
        result = preprocess_query(query)
        
        print(f"🎯 Domain:      [{result.get('domain')}]")
        print(f"🔍 RL Question: {result.get('refined_question')}\n")
        
def run_lab():
    print("=" * 60)
    print("🧠 Welcome to the Interactive Query Lab!")
    print("Type any casual insurance question below. Type 'exit' to quit.\n")
    
    while True:
        raw_query = input("👤 You (Raw Query): ")
        
        if raw_query.lower() in ['exit', 'quit']:
            print("Exiting lab. Goodbye!")
            break
            
        print("   ⏳ Processing...")
        processed_data = preprocess_query(raw_query)
        
        print(f"🎯 Target Domain:  [{processed_data.get('domain')}]")
        print(f"🔍 RL Question:    {processed_data.get('refined_question')}")
        print("-" * 60)

if __name__ == "__main__":
    # First, run the automated tests to verify the pipeline
    
    # Then, open the interactive lab for custom testing
    run_lab()