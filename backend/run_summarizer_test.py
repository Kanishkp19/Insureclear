import json
from dotenv import load_dotenv
from policy_summarizer import summarize_policy_tree

load_dotenv()

with open('test_tree.json', 'r') as f:
    tree_data = json.load(f)

print("Running summarizer...")
result = summarize_policy_tree(tree_data)

print("\n" + "="*80)
print(f"✅ SUCCESS: {result.get('total_clauses', 0)} clauses summarized by Groq Llama-3.")
print("="*80)
for i, clause in enumerate(result.get('clauses', []), 1):
    print(f"\n[{i}] {clause.get('clause_name', 'Unknown')}")
    print(f"    {clause.get('plain_english', '')}")
    if clause.get("watch_out_for"):
        print("    ⚠️  Watch out for:")
        for w in clause["watch_out_for"]:
            print(f"       - {w}")
