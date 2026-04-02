# InsureEnv — Insurance Policy Understanding Environment

An OpenEnv-compliant RL environment that trains AI agents to understand, analyze, and explain insurance policies. Uses **PageIndex** (vectorless, reasoning-based RAG) to navigate complex policy documents — no vector databases, no chunking, just LLM reasoning over document structure.

## Why insurance?

Insurance policy understanding is a genuine, high-value problem. Millions of people buy policies they don't understand, miss critical exclusions, and file claims that get denied. An agent trained in this environment learns the exact skills needed for real-world deployment: extract relevant clauses, verify coverage against exclusions, compare plans, and give nuanced recommendations with caveats.

## Tasks

| Task | Difficulty | Max Steps | What the agent must do |
|------|-----------|-----------|----------------------|
| `policy_faq` | Easy | 15 | Answer a direct question about a single policy (e.g. "What is the sum insured?") |
| `coverage_verification` | Medium | 25 | Determine if a specific scenario is covered, accounting for exclusions and waiting periods |
| `multi_plan_comparison` | Hard | 35 | Compare 3 policies, match to user profile, recommend with trade-off analysis |

### Baseline scores (heuristic agent)

| Task | Score | Steps |
|------|-------|-------|
| policy_faq | 0.60 | 4 |
| coverage_verification | 0.55 | 5 |
| multi_plan_comparison | 0.90 | 7 |
| **Average** | **0.68** | |

## Action space

```json
{"command": "extract_clause", "params": {"keyword": "maternity", "section": "Coverage"}}
{"command": "answer_question", "params": {"answer": "...", "cited_sections": ["Section 4"]}}
{"command": "compare_plans", "params": {"criteria": ["premium", "sum_insured"]}}
{"command": "recommend_plan", "params": {"plan_id": "...", "reasoning": "..."}}
{"command": "ask_clarification", "params": {"question": "..."}}
{"command": "submit", "params": {}}
```

## Observation space

Each observation includes: policy context (name, sections), user question, extracted clauses so far, current answer, comparison table, action feedback, task hints.

## Reward design

| Action outcome | Reward | Rationale |
|---------------|--------|-----------|
| Relevant clause extracted | +0.15 to +0.30 | Good intermediate step |
| Correct answer with citations | +0.40 to +0.90 | Primary objective |
| Wrong answer / hallucination | -0.30 to -0.50 | Dangerous misinformation |
| Missing critical exclusion | -0.15 | Most dangerous error in insurance |
| Irrelevant extraction | +0.02 | Not punished heavily |
| No-op / invalid command | -0.02 | Efficiency signal |
| Efficient completion bonus | +0.10 max | Rewards using fewer steps |
| Auto-submit (max steps) | score × 0.8 | 20% penalty for not finishing |

Key insight: **hallucination penalties (-0.50) are much heavier than slowness penalties (-0.02)**, teaching the agent that accuracy matters more than speed in financial advice.

## PageIndex integration

This environment uses PageIndex's vectorless RAG for document retrieval. Instead of embedding chunks in a vector database, PageIndex builds a hierarchical tree index of each policy document and uses LLM reasoning to navigate to the relevant sections — like how a human expert would read a policy.

When PageIndex API is available, the `extract_clause` action triggers reasoning-based tree search. Otherwise, it falls back to keyword matching over pre-built tree indices.

## Setup

### Local development

```bash
pip install fastapi uvicorn pydantic requests PyMuPDF
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860

# In another terminal
python baseline_inference.py --base-url http://localhost:7860

# Streamlit frontend
pip install streamlit
streamlit run streamlit_app.py
```

### Docker

```bash
docker build -t insure-env .
docker run -p 7860:7860 insure-env
```

### With PageIndex API

```bash
export PAGEINDEX_API_KEY=your_key
export OPENAI_API_KEY=your_key  # for LLM baseline
python baseline_inference.py --mode llm
```

## API endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Reset with `{task_id, seed}` |
| `/step` | POST | Execute `{command, params}` |
| `/state` | GET | Current episode state |
| `/tasks` | GET | List tasks + action schema |
| `/grader` | GET | Current grader score |
| `/baseline` | GET | Run heuristic baseline |
| `/ws` | WebSocket | Persistent sessions |

## Policy data sources

Policy PDFs sourced from IRDAI (Insurance Regulatory and Development Authority of India) approved product filings — publicly available regulatory documents.

## License

BSD-3-Clause
