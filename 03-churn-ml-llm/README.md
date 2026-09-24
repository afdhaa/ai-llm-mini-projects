# 03 - Churn ML + LLM (Hybrid)

Extends baseline tabular ML prediction by augmenting numeric risk output with LLM-generated operational briefings.

The Scikit-Learn pipeline computes numeric churn probability. The result and account activity metrics are assembled into structured context and sent to an LLM for natural-language analysis.

## Pipeline Architecture

```text
Target Record (data/target_customers.csv)
                │
                ▼
      Scikit-Learn Model
   (StandardScaler + LogisticRegression)
                │
                ▼
       Churn Probability
                │
         ┌──────┴───────┐
         ▼              ▼
   Account Metrics   Risk Score (%)
         │              │
         └──────┬───────┘
                ▼
        Structured Prompt
                │
                ▼
            LLM Client
(Gemini / OpenAI / Claude / Custom API)
                │
                ▼
   Account Briefing & Action Plan
```

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

# 4. Run risk briefing (default: Store Critical)
python src/main.py

# Or evaluate a specific merchant from data/target_customers.csv:
python src/main.py "Store Watchlist"
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
  Token Usage: Prompt = 153 | Completion = 116 | Total = 269
============================================================
```
