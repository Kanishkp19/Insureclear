import os
import time
import json
import glob
import re
import sys
from dotenv import load_dotenv
from pageindex import PageIndexClient

# 1. Load environment variables
load_dotenv()
PAGEINDEX_API_KEY = os.environ.get("PAGEINDEX_API_KEY")

if not PAGEINDEX_API_KEY:
    raise ValueError("❌ PAGEINDEX_API_KEY not found in .env file.")

# 2. Initialize PageIndex API Client
pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

# 3. Define Directory Paths
INPUT_DIR = "policy"
OUTPUT_DIR = "policyprocessed"

# Automatically create folders if they don't exist
for directory in [INPUT_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)

def clean_json_tree(tree_data):
    """Scans the generated JSON tree and strips out useless Markdown image tags."""
    if not tree_data or "result" not in tree_data or "nodes" not in tree_data["result"]:
        return tree_data
        
    img_pattern = re.compile(r'!\[.*?\]\(.*?\)')
    
    for node in tree_data["result"]["nodes"]:
        # Clean the main text block
        if "text" in node and node["text"]:
            node["text"] = img_pattern.sub('', node["text"])
            node["text"] = re.sub(r'\n\s*\n', '\n\n', node["text"]).strip()
            
        # Clean the summary block
        if "summary" in node and node["summary"]:
            node["summary"] = img_pattern.sub('', node["summary"])
            node["summary"] = re.sub(r'\n\s*\n', '\n\n', node["summary"]).strip()
            
    return tree_data

def process_single_pdf(pdf_path):
    """Submits the raw PDF to the API, then cleans and saves the resulting JSON."""
    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}_tree.json")
    
    # Skip if already processed
    if os.path.exists(json_path):
        print(f"⏭️  Skipping '{filename}' - Already processed.")
        return

    print(f"\n" + "="*50)
    print(f"📄 Processing: {filename}")
    print("="*50)
    
    start_time_total = time.time()
    
    try:
        # Step 1: Submit raw PDF directly to PageIndex API
        print("   ⏳ [1/3] Submitting raw PDF to cloud API...", end="", flush=True)
        submission = pi_client.submit_document(pdf_path)
        doc_id = submission["doc_id"]
        print("\r   ✅ [1/3] Submitted to cloud API successfully.               ")
        
        # Step 2: Polling Loop with Live Timer
        wait_seconds = 0
        sys.stdout.write(f"   ⏳ [2/3] Cloud is building reasoning tree... ({wait_seconds}s elapsed)")
        sys.stdout.flush()
        
        while not pi_client.is_retrieval_ready(doc_id):
            time.sleep(5) # Poll every 5 seconds
            wait_seconds += 5
            sys.stdout.write(f"\r   ⏳ [2/3] Cloud is building reasoning tree... ({wait_seconds}s elapsed) ")
            sys.stdout.flush()
            
        print("\r   ✅ [2/3] Reasoning tree built successfully!                   ")
        
        # Step 3: Fetch, Clean, and Save JSON
        print("   ⏳ [3/3] Fetching and cleaning JSON data...", end="", flush=True)
        raw_vectorless_doc = pi_client.get_tree(doc_id, node_summary=True)
        
        # Scrub the image tags!
        clean_vectorless_doc = clean_json_tree(raw_vectorless_doc)
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(clean_vectorless_doc, f, indent=2)
            
        total_time = round(time.time() - start_time_total, 1)
        print(f"\r   ✅ [3/3] Fetched, cleaned, and saved successfully!            ")
        print(f"🎉 Done! Saved to {json_path} (Total time: {total_time}s)")
        
    except Exception as e:
        print(f"\n❌ Failed to process '{filename}'. Error: {e}")

def run_pipeline():
    """Scans the inbox directory and processes all PDFs."""
    print("🚀 Starting Vectorless Document Ingestion Pipeline...\n")
    
    # Find all PDFs in the policy directory
    pdf_files = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"📂 No PDFs found in the '{INPUT_DIR}' folder. Drop some files there and run again!")
        return
        
    print(f"Found {len(pdf_files)} documents in the inbox.")
    
    for pdf in pdf_files:
        process_single_pdf(pdf)
        
    print("\n🏁 Pipeline execution finished!")

if __name__ == "__main__":
    run_pipeline()