# 05 - Churn Structured Outputs (Pydantic)

Production-grade customer churn evaluation enforcing **strict schema validation** via Pydantic and LangChain's `with_structured_output`.

## Why Structured Outputs?

In production architectures, free-text markdown output creates significant integration challenges:
- **Brittle Regex Parsing**: Free-text responses require regex or string slicing to extract scores and actions, leading to runtime failures on format variations.
- **Schema Drift**: Downstream consumers (REST APIs, React frontends, Postgres JSONB columns, Kafka topics) require strict, deterministic data types.
- **Zero Guarantees**: An LLM returning free text cannot guarantee that a probability is between `0.0` and `1.0` or that an enumerated risk tier matches valid backend constants.

This tier solves these issues by constraining the foundation model to return a guaranteed, validated **Pydantic Model (`ChurnAssessment`)**.

## Pipeline Architecture

```text
Target Record (data/target_customers.csv)
                │
                ▼
      Scikit-Learn Model
   (StandardScaler + LogisticRegression)
                │
                ▼
   Calibrated Churn Probability (%)
                │
                ▼
     Structured Prompt Context
                │
                ▼
LLM with Pydantic Schema Enforcement
   (llm.with_structured_output(ChurnAssessment))
                │
                ▼
   Validated Pydantic Instance
                │
         ┌──────┴────────────────┐
         ▼                       ▼
Type-Safe Python Object    Deterministic JSON
(Direct DB / API input)    (Export to file/network)
```

## Pydantic Data Contract (`src/schema.py`)

The LLM is constrained to the following schema:

```python
class ActionItem(BaseModel):
    action: str
    priority: Literal["URGENT", "HIGH", "MEDIUM", "LOW"]
    sla: str
    owner_role: str

class ChurnAssessment(BaseModel):
    merchant_name: str
    risk_tier: Literal["HIGH", "MEDIUM", "LOW", "NO RISK"]
    churn_probability: float = Field(ge=0.0, le=1.0)
    primary_drivers: list[str]
    recommended_actions: list[ActionItem]
    proposed_incentive: str
    executive_summary: str

class BatchChurnAssessment(BaseModel):
    assessments: list[ChurnAssessment]
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

# 4. Run structured evaluation:
# Mode A: Evaluate ALL target accounts in batch (Default):
python src/main.py

# Mode B: Evaluate a specific merchant:
python src/main.py "Store Watchlist"

# Export validated JSON directly to a file:
python src/main.py -o data/batch_assessments.json
python src/main.py "Store Critical" -o data/single_assessment.json
```

## Supported Providers

Configured via `AI_PROVIDER` in `.env`:
- **`gemini`** (default): Google Gemini (`gemini-2.5-flash`).
- **`openai`**: OpenAI models (`gpt-4o-mini`, etc.).
- **`anthropic`**: Anthropic models (`claude-3-5-haiku-latest`, etc.).
- **`custom`**: Any OpenAI-compatible endpoint with `AI_BASE_URL` (Ollama, Groq, vLLM, DeepSeek, Z.ai Coding Plan).

## Token Usage Tracking

Tracks exact prompt, completion, and total tokens from provider response metadata:
```text
================================================================
  Token Usage: Prompt = 842 | Completion = 215 | Total = 1,057
================================================================
```
