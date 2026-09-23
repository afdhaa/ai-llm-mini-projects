# AI & LLM Customer Churn Projects

A progressive 4-tier architecture series demonstrating customer churn prediction and retention workflows:

1. **`01-churn-ml`**: Baseline tabular machine learning (Logistic Regression).
2. **`02-churn-llm`**: Pure foundation LLM reasoning zero-shot over raw account activity metrics.
3. **`03-churn-ml-llm`**: Hybrid architecture (Scikit-Learn statistical inference + LLM narrative briefing).
4. **`04-churn-langchain`**: Autonomous agent using LangChain tool calling across ML inference, account databases, and retention SOP playbooks.

All four projects solve the same domain problem: identifying at-risk merchant accounts and determining appropriate retention strategies.

## Architectural Evolution

```text
01. Baseline Pure ML
    Tabular Data ──> Logistic Regression ──> Calibrated Churn Probability (%)

02. Pure LLM (Zero-Shot)
    Tabular Data ──> Foundation Prompt ──> Direct LLM Qualitative Assessment

03. Hybrid (ML + LLM)
    Tabular Data ──> Scikit-Learn Model ──> Probability + Context ──> LLM Briefing

04. Agentic Orchestration
    User Query ──> Autonomous LLM Agent ──> Tool Calling (ML + DB + Playbook) ──> Action Plan
```

## Quick Start

Each project is self-contained with its own dependencies and virtual environment:

```bash
# 1. Baseline ML
cd 01-churn-ml
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/train.py
python src/main.py

# 2. Pure LLM (Zero-Shot)
cd ../02-churn-llm
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/main.py

# 3. Hybrid (ML + LLM)
cd ../03-churn-ml-llm
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py

# 4. Agentic Workflow
cd ../04-churn-langchain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py
```

## Supported LLM Providers

Projects `02`, `03`, and `04` support multiple model providers configured via `.env`:

- **Google Gemini** (default): `AI_PROVIDER=gemini`
- **OpenAI**: `AI_PROVIDER=openai` (`gpt-4o-mini`, etc.)
- **Anthropic**: `AI_PROVIDER=anthropic` (`claude-3-5-haiku-latest`, etc.)
- **Custom / OpenAI-Compatible**: `AI_PROVIDER=custom` with `AI_BASE_URL` (supports Ollama, Groq, DeepSeek, vLLM, and Z.ai Coding Plan).

See `ARCHITECTURE.md` for technical diagrams and component comparisons.
