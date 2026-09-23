# 02 - Churn LLM (Zero-Shot)

Pure LLM evaluation of customer churn risk directly from raw tabular activity metrics using prompt engineering, without training a traditional machine learning model.

## Core Concept & Tradeoffs

This tier demonstrates how a foundation LLM handles tabular data zero-shot:
- **Advantage**: Immediate deployment. No model training, artifact persistence, or data labeling pipeline required.
- **Tradeoff**: Lack of statistical probability calibration. LLMs excel at qualitative diagnosis and action planning, but can produce uncalibrated or hallucinated risk probabilities on tabular numbers compared to calibrated statistical models.

## Pipeline Architecture

```text
Customer Record (data/customers.csv)
                │
                ▼
      Structured Context
(Account Metrics: transactions, active days, inactive days)
                │
                ▼
    Zero-Shot Prompt Engineering
                │
                ▼
            LLM Client
(Gemini / OpenAI / Claude / Custom API)
                │
                ▼
  Direct Risk Briefing & Action Plan
```

## Setup & Execution

```bash
# 1. Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Configure your active provider (default: Gemini)

# 3. Run zero-shot evaluation (default: Store B)
python src/main.py

# Or evaluate a specific merchant from data/customers.csv:
python src/main.py "Store D"
```

## Supported Providers

Configured via `AI_PROVIDER` in `.env`:
- **`gemini`** (default): Google Gemini (`gemini-2.5-flash`).
- **`openai`**: OpenAI models (`gpt-4o-mini`, etc.).
- **`anthropic`**: Anthropic models (`claude-3-5-haiku-latest`, etc.).
- **`custom`**: Any OpenAI-compatible endpoint with `AI_BASE_URL` (Ollama, Groq, vLLM, DeepSeek, Z.ai Coding Plan).

## Token Usage Tracking

Execution displays official API token consumption extracted directly from provider response metadata:
```text
============================================================
  Token Usage: Prompt = 151 | Completion = 180 | Total = 331
============================================================
```
