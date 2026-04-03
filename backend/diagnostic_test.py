import os
import json
import torch
import sys
from inference_universal import UniversalInference

# Ensure output is UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_diagnostic():
    print("🚀 Starting Diagnostic Test (Safe Encoding)...")
    try:
        engine = UniversalInference(model_path="./universal_selector", data_folder="./data/")
        
        doc_id = "BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree"
        question = "stolen car coverage"
        
        print(f"\n🔍 Querying '{doc_id}' with: '{question}'")
        
        # Run extraction
        payload = engine.extract_payload(question, [doc_id], confidence_threshold=0.0)
        
        # Write to file instead of printing large text
        with open("diag_result.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
        print("\n✅ Diagnostic results saved to 'diag_result.json'")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_diagnostic()
