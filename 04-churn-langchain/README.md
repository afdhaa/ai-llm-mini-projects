# 04 - Churn LangChain Agent

Demonstrates integration of **traditional tabular ML (Scikit-Learn)**, **large language models**, and **LangChain** as an agentic tool-calling orchestrator.

## Three-Component Architecture

| Component | Technology | Role & Responsibilities |
| :--- | :--- | :--- |
| **ML Inference** | Scikit-Learn (`LogisticRegression`) | Calculates numeric churn probability from merchant activity features (`models/churn_model.joblib`). |
| **Reasoning Engine** | LLM (Gemini / OpenAI / Claude / Custom) | Interprets natural language queries, reasons over tool selection, and synthesizes retention reports. |
| **Orchestrator** | LangChain Core | Manages tool registration (`@tool`), binds tools to model (`bind_tools`), and drives the autonomous execution loop. |

## Dynamic Multi-Tool Execution

The agent dynamically selects and chains four operational tools based on query context:
1. `get_target_customers`: Reads target accounts requiring evaluation from `data/target_customers.csv`.
2. `list_customers`: Lists accounts available across the historical database.
3. `predict_churn_risk`: Executes Scikit-Learn ML inference to determine churn probability and risk tier.
4. `get_retention_playbook`: Retrieves prescribed SOP policies (SLA, owner, incentive, action steps) from `data/retention_playbook.csv`.

```text
User Query: "Evaluate Store Safe and Store Critical, explain drivers, and prescribe retention actions"
  │
  ▼
[LangChain Agent Loop]
  ├── Step 1: Call `predict_churn_risk` (Store Safe & Store Critical)
  ├── Step 2: Call `get_retention_playbook` (matching risk tier)
  └── Step 3: Synthesize comprehensive operational strategy report
```

## Data Customization (`data/`)

All reference data is stored in plain CSV format:
- **`data/target_customers.csv`**: Target merchant accounts to evaluate (`customer`, `transactions`, `active_days`, `inactive_days`).
- **`data/retention_playbook.csv`**: Official retention SOP policies mapped across risk tiers (`HIGH`, `MEDIUM`, `LOW`, `NO RISK`).
- **`data/customers.csv`**: Historical dataset for training the ML pipeline (`src/train.py`).

## Setup & Execution

```bash
# 1. Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env and configure your active provider (default: Gemini)

# 3. Train model
python src/train.py

# 4. Run default evaluation (all accounts in data/target_customers.csv)
python src/main.py

# Or pass a custom query via CLI arguments:
python src/main.py "Evaluate Store Critical and prescribe immediate intervention actions"
```

## Supported Providers

Configured via `AI_PROVIDER` in `.env`:
- **`gemini`** (default): Google Gemini (`gemini-2.5-flash`).
- **`openai`**: OpenAI models (`gpt-4o-mini`, etc.).
- **`anthropic`**: Anthropic models (`claude-3-5-haiku-latest`, etc.).
- **`custom`**: Any OpenAI-compatible endpoint with `AI_BASE_URL` (Ollama, Groq, vLLM, DeepSeek, Z.ai Coding Plan).

## Token Usage Tracking

Execution tracks **cumulative multi-turn token consumption** across all agent reasoning steps:
```text
====================================================================
  Cumulative Token Usage (4 reasoning turns):
  Prompt = 3,870 | Completion = 984 | Total = 4,854
====================================================================
```
