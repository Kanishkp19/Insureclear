# InsureClear — Insurance Policy RL Environment

![openenv](https://img.shields.io/badge/openenv-compatible-blue)
![HuggingFace Space](https://img.shields.io/badge/HuggingFace-Space-orange)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-green)

An OpenEnv-compliant Reinforcement Learning environment for insurance policy understanding. An agent reads real insurance policy text using **vectorless RAG** (reasoning-based document traversal — no embeddings, no vector databases) and must answer questions about coverage, exclusions, waiting periods, and plan comparisons — with rewards based on accuracy, completeness, and correct identification of dangerous exclusions.

---

## Why this environment exists

Insurance policies are legally binding documents that most people cannot understand. A typical health insurance policy in India is 80–120 pages of dense legal language. When a claim gets rejected, the policyholder is told they "should have read clause 34(b)(ii)." They never had a fair chance.

The central challenge this environment tests is **negation with exceptions**:
```
"Natural disasters are covered under this policy
 except earthquake and volcanic eruption."
```

A naive model reads *"natural disasters are covered"* and stops. The correct answer must capture that earthquake is **not** covered — that's the clause that costs real money when missed. Every reward function in this environment is designed around this failure mode.

---

## End-to-end pipeline

InsureClear is not just an RL environment — it is a full advisory pipeline. The RL scoring system sits in the middle of a larger workflow:
```
Vectorless RAG
     │
     ▼
RL Scoring System   ◄─── scores extracted clauses from RAG
     │
     ▼
Explanation Layer   ◄─── Flan-T5: plain-English explanation of the scored answer
     │
     ▼
Multilingual Layer  ◄─── mT5: Hindi, Tamil, Spanish, Arabic
     │
     ▼
Chatbot Interface   ◄─── conversational Q&A over policy
     │
     ▼
Voice Agent         ◄─── speech in / speech out
```

Each stage is independently testable. The RL system is the core scoring mechanism — the layers above feed it clauses, the layers below consume its output.

---

## How the vectorless RAG works

Standard RAG splits documents into chunks and retrieves by embedding similarity. InsureClear does not do this.

**Vectorless RAG builds a hierarchical tree index** of each policy document at load time. The tree reflects the document's own structure — parts, sections, sub-clauses — exactly the way a human insurance expert would mentally index a policy. At query time, an LLM traverses this tree using reasoning to navigate to the relevant section rather than by nearest-vector lookup.
```
Policy Document
└── Part A — Hospitalisation Cover
    ├── Section 1 — Inpatient Care
    ├── Section 2 — Pre/Post Hospitalisation
    └── Section 3 — Exclusions
        ├── Clause 3.1 — Pre-existing diseases
        ├── Clause 3.2 — Waiting periods
        └── Clause 3.3 — Named exclusions
            ├── 3.3.1 Natural disasters except earthquake
            └── 3.3.2 Congenital conditions
```

**Why this matters for insurance:** Exclusions are always in specific sub-clauses. A vector search might retrieve "natural disasters are covered" from Section 4 while completely missing "except earthquake" from Clause 3.3.1 three pages later. Tree traversal follows the document's own logic and retrieves the full clause — coverage statement and exception together.

**Fallback:** When the vectorless RAG API is unavailable, the environment falls back to keyword matching over pre-built tree index JSON files stored in `scenarios/`.

---

## How the RL system scores RAG output

The vectorless RAG extracts a clause. The RL system then scores it.

The reward signal is produced by a fine-tuned **DeBERTa-v3 NLI judge** that checks whether the agent's answer logically entails the ground truth. This happens in two stages:

**Stage 1 — Clause quality check**
Before the agent answers, the RL system scores the extracted clause itself. A clause that drops the exception ("natural disasters are covered") scores lower than one that preserves it ("natural disasters are covered, except earthquake"). This gives the RAG component a learning signal.

**Stage 2 — Answer quality check**
After the agent forms its answer from the extracted clause, the NLI judge scores the final answer against the ground truth. Dropping an exclusion, hallucinating coverage, or contradicting the policy each produce different penalty scores.
```
Vectorless RAG extracts clause
         │
         ▼
DeBERTa checks clause completeness  →  partial reward to RAG
         │
         ▼
Agent forms answer from clause
         │
         ▼
DeBERTa checks answer vs ground truth  →  final reward to agent
```

This two-stage scoring means the RL system can distinguish between **a retrieval failure** (wrong clause extracted) and **a reasoning failure** (right clause, wrong answer).

---

## Action space

| Action type | When to use | Content field |
| --- | --- | --- |
| `extract_clause` | Agent wants to locate the relevant section before answering | The extracted policy text from vectorless RAG |
| `answer` | Agent is ready to give its final answer | The answer in plain English |
| `flag_for_review` | Agent cannot determine the answer from the policy | Reason for uncertainty |

**Action schema (Pydantic):**
```python
class Action(BaseModel):
    action_type: Literal["extract_clause", "answer", "flag_for_review"]
    content: str        # the answer or extracted clause
    confidence: float   # agent self-reported confidence, 0.0–1.0
```

---

## Observation space

At each step, the agent receives:
```python
class Observation(BaseModel):
    policy_text: str    # clause(s) retrieved by vectorless RAG
    question: str       # the question the agent must answer
    task_id: int        # 1, 2, or 3
    context: dict       # {"prev_score": float, "step": int, "clause_score": float}
```

The `context` field now carries both the previous answer score **and** the clause quality score from Stage 1 scoring, so the agent can decide whether to re-extract before answering. Each episode allows up to 5 steps.

---

## Reward function
```python
class Reward(BaseModel):
    score: float          # −1.0 to +1.0
    reason: str           # "entails" | "neutral" | "contradicts" | "no_attempt"
    partial_credits: dict # NLI probabilities + clause score + exception check
```

| Agent behaviour | Score | Reasoning |
| --- | --- | --- |
| Correct answer, all exclusions named | `+1.0` | Full credit |
| Correct answer, one exclusion missing | `+0.7` | Partial — still actionable |
| Correct answer, no exclusions cited | `+0.4` | Misleading for the user |
| Answer is plausible but unverifiable | `+0.1` | Weak signal |
| No answer / flag without attempt | `0.0` | No information |
| Hallucinated coverage not in policy | `−0.5` | Actively dangerous |
| Says covered when explicitly excluded | `−0.5` | Critical failure |

The **−0.5 hallucination penalty** is heavier than any efficiency penalty. In insurance, a wrong answer isn't just unhelpful — it can cause real financial harm.

---

## Tasks

### Task 1 — Fact lookup (easy)

**Objective:** Find a specific factual value in the policy text.

**Example scenario:**
```
Policy text: "Maternity expenses including pre and post natal care shall be covered
after a waiting period of 9 months from the date of commencement of the policy."

Question: "What is the waiting period for maternity benefits?"
```

**Grader:** Extracts the number from the agent's answer and compares to ground truth. Partial credit for correct value in wrong format (e.g. "3 years" vs "36 months").

**Baseline score (GPT-4o):** ~0.72

---

### Task 2 — Coverage and exclusions (medium)

**Objective:** Determine whether a specific item is covered, and if not, identify the exclusion by name.

**Example scenario:**
```
Policy text: "Natural disasters including flood, storm, and cyclone are covered
under Section 4 of this policy, except earthquake, volcanic eruption, and damage
caused by subsidence or landslip, for which no claim shall be entertained."

Question: "Is earthquake damage covered under this policy?"
```

**Grader:** NLI judge checks whether the agent's answer entails the ground truth. Additionally checks that all required exceptions are named. Agents that say "not covered" without naming "earthquake" and "volcanic eruption" score 0.4, not 1.0.

**Baseline score (GPT-4o):** ~0.61

---

### Task 3 — Compare three policies (hard)

**Objective:** Given summaries of three insurance plans, recommend the best option for a given user profile, with specific clause citations.

**Example scenario:**
```
Policy A: "Maternity covered after 9 months. Sub-limit: ₹50,000."
Policy B: "Maternity covered after 24 months. Sub-limit: ₹1,00,000."
Policy C: "Maternity not covered. Rider available at extra premium."

User profile: "First-time buyer, planning a family within 2 years."

Question: "Which plan offers the best maternity coverage for this user?"
```

**Grader:** Extracts the recommended plan, compares to the answer key. Bonus credit for citing the specific clause that justifies the recommendation. Penalty for recommending without reasoning.

**Baseline score (GPT-4o):** ~0.54

---

## Explanation layer

After the RL system produces a scored answer, the Explanation layer generates a **plain-English explanation** of why the coverage decision was made, citing the specific clause.

Model: fine-tuned `google/flan-t5-base`
```
RL answer:    "Earthquake damage is not covered. See Clause 3.3.1."
Explanation:  "Your policy covers most natural disasters like floods and storms,
               but specifically excludes earthquakes. This means if an earthquake
               damages your property, your insurer will not pay the claim."
```

The explanation is generated from the scored clause, not from the raw policy text — ensuring the explanation is consistent with the scoring decision.

---

## Multilingual layer

The explanation is then translated by a fine-tuned `google/mt5-base` model.

Supported languages: **Hindi, Tamil, Spanish, Arabic**

The multilingual layer operates on the explanation output, not the raw policy text. This ensures translated answers are plain English first, legal text never.

---

## Chatbot interface

The chatbot wraps the full pipeline — RAG → RL → Explanation → Translation — in a conversational interface. Users can ask follow-up questions, and the system maintains context across turns using the full conversation history in each request.

The chatbot is available at `/chat` via the FastAPI server and as a Streamlit frontend (`streamlit_app.py`).

---

## Voice agent

The voice agent adds speech input and speech output to the chatbot layer. A user speaks their question, the pipeline runs end-to-end, and the answer is read back aloud in the user's language.
```
User speaks → STT → Chatbot pipeline → TTS → User hears answer
```

The voice agent is designed for low-literacy users who cannot read policy documents at all — the population most harmed by incomprehensible insurance language.

---

## Baseline scores

Run `inference.py` to reproduce these scores:
```
Task 1 (fact lookup):         0.72
Task 2 (coverage+exclusions): 0.61
Task 3 (policy comparison):   0.54
Average:                      0.62
```

A fine-tuned agent trained on InsureClear scenarios should reach 0.80+ average.

---

## Setup and usage

### Option 1: Run with Docker (recommended)
```bash
git clone https://github.com/YOUR_USERNAME/insureclear
cd insureclear

docker build -t insureclear .
docker run -p 7860:7860 insureclear
```

Verify the environment is running:
```bash
curl http://localhost:7860/health
# {"status": "ok"}
```

### Option 2: Run locally
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn api:app --host 0.0.0.0 --port 7860
```

---

## API reference

All endpoints are REST. The environment runs as a FastAPI server.

### `GET /health`
Returns 200 if the environment is running.

### `POST /reset?task_id={1|2|3}`
Loads a scenario and returns the initial observation, including the vectorless RAG extracted clause.

### `POST /step`
Submit an agent action. Returns next observation, reward (including clause score), and done flag.

**Request:**
```json
{
  "action_type": "answer",
  "content": "The waiting period for maternity benefits is 9 months.",
  "confidence": 0.9
}
```

**Response:**
```json
{
  "observation": { "policy_text": "...", "question": "...", "task_id": 1,
                   "context": {"prev_score": 1.0, "clause_score": 0.95, "step": 1} },
  "reward": { "score": 1.0, "reason": "entails",
              "partial_credits": {"entails": 0.97, "neutral": 0.02, "contradicts": 0.01,
                                  "clause_completeness": 0.95, "exception_check": true} },
  "done": true
}
```

### `GET /explain`
Returns the plain-English explanation for the last scored answer.

### `GET /translate?lang={hi|ta|es|ar}`
Returns the translated explanation in the specified language.

### `POST /chat`
Conversational endpoint. Accepts `{message, history, lang}`, returns full pipeline output.

### `GET /state`
Returns the current environment state dict.

---

## Running the baseline inference script
```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="your-api-key-here"

python inference.py
```

---

## Project structure
```
insureclear/
├── inference.py              ← baseline script
├── env.py                    ← InsureClearEnv: reset() / step() / state()
├── api.py                    ← FastAPI server
├── streamlit_app.py          ← chatbot frontend
├── openenv.yaml              ← environment metadata
├── Dockerfile
├── requirements.txt
│
├── pipeline/
│   ├── vectorless_rag.py     ← tree index builder + LLM-guided traversal
│   ├── judge.py              ← DeBERTa NLI judge (clause scoring + answer scoring)
│   ├── explainer.py          ← Flan-T5 plain-English explanation
│   ├── translator.py         ← mT5 multilingual output
│   ├── chatbot.py            ← conversational wrapper
│   ├── voice.py              ← STT / TTS voice agent
│   └── verification.py       ← two-stage scoring loop
│
├── scenarios/
│   ├── task1/                ← fact lookup scenarios (JSON + tree index)
│   ├── task2/                ← coverage+exclusion scenarios (JSON + tree index)
│   └── task3/                ← policy comparison scenarios (JSON + tree index)
│
└── models/
    ├── deberta-insurance-nli/          ← fine-tuned NLI judge
    ├── legalbert-insurance-extraction/ ← fine-tuned clause extractor (fallback)
    ├── flan-t5-insurance-explanation/  ← fine-tuned explanation model
    └── mt5-insurance-translation/      ← fine-tuned multilingual model
```

---

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `API_BASE_URL` | Yes (inference) | LLM API endpoint |
| `MODEL_NAME` | Yes (inference) | Model identifier |
| `HF_TOKEN` | Yes (inference) | API key |
| `VECTORLESS_RAG_API_KEY` | No | Key for vectorless RAG API; falls back to tree index keyword search if absent |
| `JUDGE_ENTAILS_THRESHOLD` | No | NLI pass threshold, default 0.92 |
| `JUDGE_FLAG_THRESHOLD` | No | NLI flag threshold, default 0.80 |
| `DEFAULT_LANG` | No | Default output language, default `en` |

---

## Model stack

| Model | Role | Size |
| --- | --- | --- |
| Vectorless RAG (tree traversal) | Document retrieval — no embeddings | — |
| `microsoft/deberta-v3-base` (fine-tuned) | NLI judge — clause scoring + answer scoring | 184M |
| `nlpaueb/legal-bert-base-uncased` (fine-tuned) | Fallback clause extraction (keyword mode) | 110M |
| `google/flan-t5-base` (fine-tuned) | Plain-English explanation generation | 250M |
| `google/mt5-base` (fine-tuned) | Translation: Hindi, Tamil, Spanish, Arabic | 580M |

All models run sequentially. Peak RAM ~1.2GB. Fits within the 8GB memory constraint.

---

## The negation problem — why this environment is hard

Standard NLP benchmarks don't penalise dropping exceptions. This environment does:
```
Policy:    "Natural disasters are covered except earthquake."
Bad agent: "Natural disasters are covered."  → score: −0.5 (contradicts)
Good agent: "Natural disasters are covered, but earthquake is excluded." → score: +1.0
```

Vectorless RAG is specifically designed to help here — tree traversal retrieves the coverage clause and its exception sub-clause together, because they live in the same branch of the document tree. Vector search has no reason to retrieve the exception; it's in a different chunk.

---

## License

MIT License. Policy text in scenario files is synthetic, generated for training and evaluation purposes only.

---

## Citation
```
@software{insureclear2026,
  title  = {InsureClear: An RL Environment for Insurance Policy Understanding},
  year   = {2026},
  url    = {https://huggingface.co/spaces/YOUR_USERNAME/insureclear}
}
```