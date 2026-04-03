import json
import logging
from inference_universal import UniversalInference
from agent_pipeline import clean_json_tree

# Suppress HuggingFace warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

# Load a local tree file to simulate what pi_client.get_tree() returns
with open("data/new-complete-health-insurance-brochure_tree.json") as f:
    tree = json.load(f)

# 1. Tree structure
print("--- 1. Tree structure ---")
print("TOP LEVEL KEYS:", list(tree.keys()))
if "result" in tree:
    if isinstance(tree["result"], dict):
        print("RESULT KEYS:", list(tree["result"].keys()))
        print("NODE COUNT:", len(tree["result"].get("nodes", [])))
        first_node = tree["result"]["nodes"][0] if tree["result"].get("nodes") else None
    elif isinstance(tree["result"], list):
        print("RESULT IS A LIST (Direct flatten structure)")
        print("NODE COUNT:", len(tree["result"]))
        first_node = tree["result"][0] if tree["result"] else None

    if first_node:
        print("FIRST NODE KEYS:", list(first_node.keys()))
        print("FIRST NODE PREVIEW:", {k: str(v)[:50] for k, v in first_node.items()})

# 2. After clean_json_tree
print("\n--- 2. After clean_json_tree ---")
cleaned = clean_json_tree(tree)
if "result" in cleaned:
    if isinstance(cleaned["result"], list):
        nodes = cleaned["result"]
    else:
        nodes = cleaned["result"].get("nodes", [])
    print("NODES AFTER CLEAN:", len(nodes))
    if nodes:
        print("SAMPLE NODE KEYS:", list(nodes[0].keys()))

# 3. After ingest_tree
print("\n--- 3. After ingest_tree ---")
ui = UniversalInference()
ui.ingest_tree("User_Uploaded_Policy", cleaned)
ingested = ui.json_docs.get("User_Uploaded_Policy", [])
print("INGESTED NODE COUNT:", len(ingested))
if ingested:
    print("SAMPLE INGESTED NODE KEYS:", list(ingested[0].keys()))

# 4. Does _extract_nodes recurse correctly
print("\n--- 4. Recurse correctly? ---")
if first_node:
    print("HAS CHILDREN KEY ('nodes' in first_node):", "nodes" in first_node)
    
# 5. Pre-retrieval scoring
print("\n--- 5. Pre-retrieval scoring ---")
question = "what is diet consultation rider"
nodes = ui.json_docs.get("User_Uploaded_Policy", [])
print(f"Total nodes to search: {len(nodes)}")
matches = 0
for n in nodes:
    text_lower = n['text'].lower()
    if "diet" in text_lower or "consultation" in text_lower or "rider" in text_lower:
        print("MATCH FOUND:")
        print("  ID:", n['id'])
        print("  PATH:", n.get('path', 'NO PATH FIELD'))
        print("  SUMMARY:", n['summary'][:100].replace("\n", " "))
        print("-" * 40)
        matches += 1

print(f"\nTotal matches found containing 'diet', 'consultation', or 'rider': {matches}")
