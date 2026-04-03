# VectorlessPI

VectorlessPI is an intelligent pipeline for ingesting insurance property documents and interactively routing/extracting information without traditional vector databases. It leverages large language models (via Google Gemini) and the PageIndex API to create logical reasoning trees out of complex PDFs. The complete system includes a fully functional LangGraph agent pipeline that routes queries, mimics RL-based information extraction, and serves simplified, empathetic explanations.

## Features

- **Document Processing**: Submits raw PDFs to the PageIndex API, extracting structured node hierarchies (reasoning trees) instead of vector embeddings.
- **Intelligent Query Routing**: Reformats casual user inquiries into strict, formalized RL queries and auto-categorizes them by domain (Life, Health, Property, etc.).
- **Agent Pipeline**: A state machine (built with LangGraph) that pipes input from a raw query, parses it through the router, forwards it to a mock Reinforcement Learning (RL) extraction node, and translates the retrieved clauses into empathetic human-readable answers.
- **Interactive Lab**: CLI tools for bulk-testing queries or running an interactive chat simulation for query refining.

## Files Structure

- `agent_pipeline.py` - Core LangGraph agent integrating Gemini and mocking an RL component.
- `process_policies.py` - Script reading from `policy/`, sending PDFs to PageIndex API, and dumping cleaned logic trees to `policyprocessed/`.
- `query_router.py` - Pure utilities to handle domain classification and question refinement using Gemini models.
- `query_lab.py` - A testing ground with automated query batches and a manual interactive loop to test preprocessing reliability.
- `requirements.txt` - Project dependencies.

## Prerequisites

- Python 3.8+
- [Google GenAI API Key](https://aistudio.google.com/app/apikey)
- [PageIndex API Key] (for Vectorless extraction)

## Setup Instructions

1. Clone this repository or download the project files.
2. Setup a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory and add your keys:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   PAGEINDEX_API_KEY=your_pageindex_key_here
   ```

## Usage

**Process Policies:**  
Populate the `policy/` directory with PDF files you wish to process, then run:
```bash
python process_policies.py
```
This script will produce JSON logic trees inside `policyprocessed/`.

**Test Query Engine:**  
Run automated tests or interactive questions locally to ensure logic behaves normally:
```bash
python query_lab.py
```

**Run LangGraph Pipeline Simulator:**  
Simulate an end-to-end conversation workflow:
```bash
python agent_pipeline.py
```

## Future Scope

Replace the mocked RL (Reinforcement Learning) module block conceptually represented in `agent_pipeline.py` with an actual RL policy retrieval model.
