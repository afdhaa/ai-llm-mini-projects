# Architecture Overview

This repository demonstrates five progressive architectures solving the same domain problem: **Customer Churn Prediction and Retention Strategy**.

```text
01. Pure ML           02. Pure LLM          03. Hybrid (ML + LLM)     04. Agentic AI        05. Structured Output
┌──────────────┐      ┌──────────────┐      ┌────────────────────┐    ┌────────────────────┐ ┌────────────────────┐
│ Scikit-Learn │      │ Foundation   │      │ Scikit-Learn (ML)  │    │ LangChain Agent    │ │ Pydantic Schema    │
│ Statistical  │ ───> │ Zero-Shot    │ ───> │        +           │ ──>│ Tool Calling       │─>│ Strict Contract    │
│ Pipeline     │      │ Prompting    │      │ LLM Briefing       │    │ Dynamic Loop       │ │ Type-Safe JSON     │
└──────────────┘      └──────────────┘      └────────────────────┘    └────────────────────┘ └────────────────────┘
```

---

## Tier 1: Baseline Machine Learning (`01-churn-ml`)

Standard tabular machine learning pipeline using Scikit-Learn without LLM dependencies.

```text
Customer Activity Data (CSV)
            │
            ▼
Feature Preprocessing (StandardScaler)
            │
            ▼
Logistic Regression Pipeline
            │
            ▼
Churn Probability & Percentage Output
```

- **Characteristics**: Fast, deterministic, statistically calibrated probabilities.
- **Limitation**: Produces numeric scores only; lacks conversational explanation or dynamic reasoning.
- **Artifact**: `models/churn_model.joblib`.

---

## Tier 2: Pure Foundation LLM (`02-churn-llm`)

Direct zero-shot prompting of foundation models over raw tabular activity metrics, bypassing traditional ML model training.

```text
Customer Activity Data (CSV)
            │
            ▼
Raw Feature Extraction (transactions, active days, inactive days)
            │
            ▼
Zero-Shot Structured Prompt
            │
            ▼
LLM Client (Gemini / OpenAI / Claude / Custom API)
            │
            ▼
Qualitative Risk Tier & Narrative Assessment
```

- **Characteristics**: Zero training required; immediate deployment; rich qualitative behavioral explanations.
- **Limitation**: Subjective probability estimations; uncalibrated risk assessments on raw numerical data.
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Tier 3: Hybrid Architecture (`03-churn-ml-llm`)

Combines statistical accuracy from Scikit-Learn with qualitative reasoning from an LLM.

```text
Customer Activity Data (CSV)
            │
            ▼
Scikit-Learn Churn Pipeline
            │
            ▼
    Churn Probability
            │
      ┌─────┴────────────────┐
      ▼                      ▼
Activity Metrics       Risk Score (%)
      │                      │
      └───────────┬──────────┘
                  ▼
          Customer Context
                  │
                  ▼
              LLM Client
      (Gemini / OpenAI / Claude / Custom)
                  │
                  ▼
      CS Account Risk Briefing (Free-Text)
```

- **Characteristics**: Best of both worlds. The statistical model delivers calibrated probability percentages while the LLM interprets the drivers and formulates an actionable intervention plan.
- **Limitation**: Free-text output is difficult to reliably parse for downstream databases and API pipelines.
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Tier 4: Autonomous Agent with Tool Calling (`04-churn-langchain`)

The LLM acts as an autonomous agent using LangChain tool calling. Given a query, the agent dynamically determines which tools to invoke, executes them against local data and ML models, and synthesizes the findings into an actionable retention plan.

```text
User Query / Task
       │
       ▼
LLM Agent (LangChain)
       │
       ├─────────────────────────────────────────┐
       │ (Autonomous Tool Loop)                  │
       ▼                                         ▼
   1. get_target_customers           3. predict_churn_risk
      (data/target_customers.csv)       (Scikit-Learn ML Model)
       │                                         │
       ▼                                         ▼
   2. list_customers                 4. get_retention_playbook
      (Historical Database)             (data/retention_playbook.csv)
       │                                         │
       └────────────────────┬────────────────────┘
                            │ (Tool Observations)
                            ▼
                    LLM Synthesis
                            │
                            ▼
        Executive Account Summary & Action Plan
```

### Agentic Loop Sequence Diagram

```text
User            LangChain Runner                LLM Brain (Remote)         Local Tools (Python)
 │                     │                                │                           │
 │── User Query ──────>│                                │                           │
 │                     │── Prompt + Tool Schemas ──────>│                           │
 │                     │<─ Tool Call Intent ────────────│                           │
 │                     │   (e.g., get_target_customers) │                           │
 │                     │                                │                           │
 │                     │── Execute Local Function ─────────────────────────────────>│
 │                     │<─ Return Tool Output (CSV records) ────────────────────────│
 │                     │                                │                           │
 │                     │── Send Observation ───────────>│                           │
 │                     │<─ Tool Call Intent ────────────│                           │
 │                     │   (e.g., predict_churn_risk)   │                           │
 │                     │                                │                           │
 │                     │── Execute ML Inference (.joblib) ─────────────────────────>│
 │                     │<─ Return Churn Probabilities ──────────────────────────────│
 │                     │                                │                           │
 │                     │── Send Observation ───────────>│                           │
 │                     │<─ Final Response (No tools) ───│                           │
 │<── Strategy Report ─│                                │                           │
```

- **Characteristics**: Multi-turn reasoning; dynamic query resolution; autonomous decision making; integrates disparate databases, models, and policy playbooks.
- **Token Accounting**: Cumulative multi-turn usage summation across all reasoning iterations.

---

## Tier 5: Production Structured Outputs (`05-churn-structured-outputs`)

Replaces free-text output with a strictly validated, type-safe Pydantic model (`ChurnAssessment`) via LangChain's `with_structured_output`.

```text
Customer Record (data/customers.csv)
                │
                ▼
      Scikit-Learn Pipeline
  (Calibrated Churn Probability: 0.0 - 1.0)
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
         ┌──────┴────────────────┐
         ▼                       ▼
Type-Safe Python Object    Deterministic JSON
(Direct DB / API input)    (Export to file/network)
```

- **Characteristics**: Production contract guarantees. Eliminates regex parsing; guarantees numerical ranges (`ge=0.0, le=1.0`), strict categorical enums (`Literal`), and nested arrays of validated objects (`ActionItem`).
- **Downstream Readiness**: Direct serialization to Postgres JSONB, REST API response bodies, or message queues.
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Architecture Comparison Matrix

| Dimension | 01 - Churn ML | 02 - Churn LLM | 03 - Churn ML + LLM | 04 - Churn LangChain | 05 - Structured Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Paradigm** | Traditional ML | Foundation LLM | Hybrid (ML + LLM) | Agentic AI | Schema-Enforced AI |
| **Model Training** | Required (Scikit-Learn) | None | Required (Scikit-Learn) | Required (Scikit-Learn) | Required (Scikit-Learn) |
| **Probability Source** | Calibrated (Statistical) | Heuristic Estimate | Calibrated (Statistical) | Calibrated (via ML Tool) | Calibrated (Statistical) |
| **Output Type** | Numeric float (`.joblib`) | Free-Text Narrative | Free-Text Narrative | Free-Text Narrative | **Validated Pydantic / JSON** |
| **API Contract** | None | None (Unstructured) | None (Unstructured) | None (Unstructured) | **Guaranteed Schema** |
| **Control Flow** | Static Sequential | Static Sequential | Static Sequential | Dynamic Autonomous Loop | Static Sequential |
| **Tool Execution** | None | None | None | Dynamic (4 Tools) | None (Schema Binding) |
| **Runtime Stack** | Scikit-Learn | LLM SDK | Scikit-Learn + LLM SDK | Scikit-Learn + LangChain | Scikit-Learn + LangChain + Pydantic |
| **Token Usage** | None (Local Compute) | Single-Turn (~300) | Single-Turn (~270) | Cumulative (~4.8k) | Single-Turn (~900) |
