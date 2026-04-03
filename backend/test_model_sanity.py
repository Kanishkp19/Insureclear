import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import re

def test_on_self():
    model_path = "./universal_selector"
    print(f"🧪 Testing model at {model_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=1)
    model.eval()

    test_pairs = [
        ["What is the free look period?", "What is the free look period?"],
        ["Is cancer covered?", "This policy covers cancer treatment and chemotherapy."],
        ["What is the premium?", "The total premium payable for this policy is 5000 rupees."]
    ]

    print("\n📊 Cross-Encoder Results:")
    for q, c in test_pairs:
        inputs = tokenizer([[q, c]], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits.squeeze(-1)
            prob = torch.sigmoid(logits).item()
        print(f"  Q: {q}")
        print(f"  C: {c}")
        print(f"  Score: {prob:.4f}")
        print("-" * 20)

if __name__ == "__main__":
    test_on_self()
