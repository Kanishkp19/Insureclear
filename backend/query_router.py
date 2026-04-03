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

# 2. Initialize the Gemini Client globally so it doesn't reconnect on every query
client = genai.Client(api_key=gemini_key)

def preprocess_query(user_query, current_ui_selection="None"):
    """
    Takes a raw user query, categorizes the domain, and expands it into 
    a highly detailed, formal question for the downstream RL extraction model.
    """
    prompt = f"""
    You are an expert Insurance QA Pre-processor.
    
    User Query: "{user_query}"
    
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
        print(f"❌ Error during preprocessing: {e}")
        # Failsafe: If the API fails, return the original query so the pipeline doesn't crash
        return {"domain": "UNKNOWN", "refined_question": user_query}