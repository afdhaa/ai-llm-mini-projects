# 10 - Churn Platform (Unified AI Full-Stack Platform)

> **Enterprise Full-Stack Platform unifying Tiers 01 through 09 into an interactive web dashboard powered by a Flask REST API backend and a React 18 frontend with dynamic in-browser model configuration.**

---

## 🎯 What is Tier 10?

In Tiers `01` through `09`, each stage of the churn retention learning path was executed via terminal CLI scripts (`python src/main.py`). While educational, real-world deployment requires:
1. **Interactive Web Workspace:** Allowing analysts, executives, and engineers to visually explore, compare, and test all 9 tiers side-by-side.
2. **Dynamic In-UI Model Configuration:** Changing AI providers, base URLs, models, and API keys directly from the web browser without hardcoding secrets in `.env` or restarting servers.
3. **Web-Based Human-in-the-Loop Console:** Enabling operators to review high-impact retention proposals, toggle actions item-by-item, steer agents with custom directives, and trigger live API dispatches.

---

## 🏗️ Full-Stack System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│ REACT FRONTEND (React 18 + Vite + Tailwind CSS + Lucide Icons)        │
│                                                                        │
│ [⚙️ Model Config]  [Customer Selector]                                │
│         │                  │                                           │
│         ▼                  ▼                                           │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ SIDEBAR (9 Dedicated Menus):                                       │ │
│ │  Phase 1: 01. Pure ML | 02. Pure LLM | 03. Hybrid | 04. Agent     │ │
│ │  Phase 2: 05. Schema  | 06. Guarded  | 07. Evals  | 08. RAG       │ │
│ │  Phase 3: 09. LangGraph Multi-Agent State Machine & HITL Console   │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST + Dynamic Headers:
                                    │ x-ai-provider, x-ai-base-url,
                                    │ x-ai-api-key, x-ai-model
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FLASK BACKEND REST API (Python 3.13)                                   │
│                                                                        │
│ ├── /api/settings/test-connection (Live model ping & latency benchmark)│
│ ├── /api/customers                (Enriched target customer profiles)  │
│ ├── /api/tier01/predict           (Sub-ms Scikit-Learn inference)      │
│ ├── /api/tier02/evaluate          (Zero-shot qualitative prompting)    │
│ ├── /api/tier03/briefing          (Calibrated hybrid executive brief)  │
│ ├── /api/tier04/chat              (ReAct autonomous agent + tool calls)│
│ ├── /api/tier05/structured        (Pydantic contracts single/batch)    │
│ ├── /api/tier06/guarded           (3-layer injection defense & sandbox)│
│ ├── /api/tier07/benchmark         (Deterministic rules + LLM-as-Judge) │
│ ├── /api/tier08/rag               (Ticket signals & root cause override)│
│ ├── /api/tier09/evaluate          (LangGraph state machine HITL pause) │
│ ├── /api/tier09/action            (Approve, Selective, Steer, Reject)  │
│ └── /api/tier09/audit             (Persisted operational audit trail)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Dynamic AI Model Configuration (Zero `.env` Dependency)

Users can configure the AI provider and credentials directly from the top-right **[⚙️ Model Config]** button in the Web UI:

- **Storage:** Persisted locally in browser `localStorage` per-user.
- **Request Injection:** Transmitted on every HTTP request via custom headers (`x-ai-provider`, `x-ai-base-url`, `x-ai-api-key`, `x-ai-model`).
- **Quick 1-Click Presets:**
  - **Z.ai Coding Plan:** `https://api.z.ai/api/coding/paas/v4` + `GLM-5.3-Flash`.
  - **OpenAI:** `https://api.openai.com/v1` + `gpt-4o-mini`.
  - **Google Gemini:** `gemini-2.5-flash`.
  - **Anthropic Claude:** `claude-3-5-haiku-latest`.
  - **Ollama / Local:** `http://localhost:11434/v1` + `llama3.1`.
- **Live Latency Benchmark:** Built-in **"Test Connection"** ping button measuring real-time API latency.

---

## 📋 The 9 Dedicated Web Menus

| # | Menu Name | Architectural Focus | Key UI Capabilities |
|---|---|---|---|
| **01** | **Pure ML Baseline** | Scikit-Learn Logistic Regression | Interactive feature sliders (`transactions`, `active_days`, `inactive_days`), sub-millisecond gauge %, and historical dataset inspector. |
| **02** | **Pure Foundation LLM** | Zero-Shot Qualitative Prompting | Customer picker, side-by-side prompt vs raw narrative output, and token economics. |
| **03** | **Hybrid (ML + LLM)** | Statistical Certainty + Narrative | Split view contrasting exact calibrated ML percentage against the AI-generated account briefing. |
| **04** | **Autonomous Agent** | LangChain Tool Calling (ReAct) | Interactive agent chat with step-by-step tool execution timeline (`predict_churn_risk`, `get_retention_playbook`). |
| **05** | **Structured Outputs** | Pydantic Schema Contracts | Toggle between single-customer evaluation and 5-account batch processing with guaranteed JSON contracts. |
| **06** | **Guarded Agent** | 3-Layer Security Perimeter | Adversarial attack playground testing prompt injections, Golang code smuggling, and jailbreaks against the security layers. |
| **07** | **Automated Evals** | LLM-as-a-Judge Benchmarking | Evaluates test cases (`TC-01` to `TC-10`) across deterministic programmatic rules and model-graded rubrics. |
| **08** | **Contextual Support RAG** | Unstructured Customer Signals | Semantic support ticket viewer contrasting tone-deaf discount vouchers against genuine technical/financial root causes. |
| **09** | **LangGraph State Machine** | Multi-Agent Deliberation & HITL | Real-time multi-agent console (Tech, Finance, Supervisor) with web-based Human-in-the-Loop decision bar (Approve, Selective, Steer, Reject) and live action dispatch. |

---

## 🚀 Quick Start Guide

### 1. Start the Flask Backend (Port 5001)

```bash
cd 10-churn-platform/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# Backend running on http://127.0.0.1:5001
```

### 2. Start the React Frontend (Port 3000)

```bash
cd 10-churn-platform/frontend
pnpm install
pnpm dev
# Frontend accessible at http://localhost:3000
```

### 3. Open in Browser & Configure Model

1. Open `http://localhost:3000` in your web browser.
2. Click **[⚙️ Model Config]** on the topbar.
3. Select your provider preset (e.g. **Z.ai Coding Plan**), paste your API key, and click **Test Connection**.
4. Explore any of the 9 menus from the sidebar!
