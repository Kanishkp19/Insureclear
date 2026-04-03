import json
import torch
import glob
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class UniversalInference:
    def __init__(self, model_path="./models/universal_selector", data_folder="./data/"):
        print(f"⏳ Loading Cross-Encoder from {model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=1)
        self.model.eval()
        
        self.json_docs = {}
        for filepath in glob.glob(os.path.join(data_folder, "*.json")):
            doc_id = os.path.basename(filepath).replace(".json", "")
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                nodes = []
                self._extract_nodes(data.get('result', data), nodes)
                # Filter valid items
                self.json_docs[doc_id] = [n for n in nodes if n["id"] and n["text"]]
                
    def _extract_nodes(self, data, nodes_list):
        if isinstance(data, list):
            for item in data:
                self._extract_nodes(item, nodes_list)
        elif isinstance(data, dict):
            node_id = data.get("node_id", data.get("id"))
            if node_id:
                summary = str(data.get("prefix_summary", data.get("summary", "")))
                text = str(data.get("text", ""))
                if len(summary) < 5: summary = text[:100] # fallback
                
                nodes_list.append({
                    "id": str(node_id),
                    "summary": summary,
                    "text": text
                })
            if "nodes" in data:
                self._extract_nodes(data["nodes"], nodes_list)

    def extract_payload(self, question, target_document_ids, confidence_threshold=0.15):
        """
        Extracts the best clauses and formats them into the JSON payload for the Explainer LLM.
        """
        payload = {
            "user_question": question,
            "selected_clauses": []
        }
        
        with torch.no_grad():
            for doc_id in target_document_ids:
                if doc_id not in self.json_docs:
                    payload["selected_clauses"].append({
                        "document_id": doc_id,
                        "node_id": "Error",
                        "confidence_score": 0.0,
                        "text": "[ DOCUMENT NOT FOUND IN DATABASE ]"
                    })
                    continue
                    
                nodes = self.json_docs[doc_id]
                pairs = [[question, n['summary']] for n in nodes]
                
                inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
                logits = self.model(**inputs).logits.squeeze(-1)
                
                # Convert logits map to probability distribution matching RL training
                probs = torch.softmax(logits, dim=0) 
                
                best_idx = torch.argmax(probs).item()
                best_prob = probs[best_idx].item()
                best_node = nodes[best_idx]
                
                payload["selected_clauses"].append({
                    "document_id": doc_id,
                    "node_id": best_node['id'],
                    "confidence_score": round(best_prob, 4),
                    "text": best_node['text']
                })
                    
        return payload

# --- TEST THE INFERENCE PIPELINE ---
if __name__ == "__main__":
    # Simulate the LLM Router passing us two documents to compare
    documents_to_check = ["BAJAJ-ALLIANZ-MOTOR-POLICY-WORDING_tree", "policy_vectorless_document"]
    question = "Does my policy cover me if my car is stolen?"
    
    # Initialize pipeline
    inference_engine = UniversalInference()
    
    # Generate the JSON payload for the Explainer LLM
    final_payload = inference_engine.extract_payload(question, documents_to_check)
    
    # Print it out exactly as the Explainer LLM will receive it
    print("\n" + "="*50)
    print(json.dumps(final_payload, indent=2))
    print("="*50 + "\n")
