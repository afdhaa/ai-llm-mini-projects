# From Machine Learning to Modern AI: A Hands-on Churn Case Study

> **A progressive learning roadmap designed to bridge the gap between classical Machine Learning and modern Generative AI engineering through a real-world business use case.**

---

## 🎯 Why This Repository Exists

Most tutorials teach **Machine Learning** (Scikit-Learn, tabular data, statistical metrics) and **Generative AI** (LLMs, LangChain, autonomous agents) in complete isolation. Beginners and engineers often struggle to answer:

1. **Where does classical Machine Learning stop, and where does Generative AI actually add value?**
2. **Can an LLM replace an ML model for tabular predictions? Should it?**
3. **How do we evolve a bare probability score into an autonomous, action-taking system?**
4. **How do we apply production-applicable patterns (schema validation, defensive guardrails, automated evals) to an experimental LLM prototype?**

This repository answers those questions by exploring **the exact same business problem across 8 progressive architectural tiers**—taking you step-by-step from a simple Logistic Regression model to an autonomous agent with defensive guardrails, automated evals, and contextual RAG.
---

## 💡 The Real-World Use Case: Customer Churn & Retention

**Customer Churn** (identifying customers or merchant accounts at risk of leaving) is one of the most critical challenges in SaaS, FinTech, and e-commerce. It is also the ideal learning vehicle because it inherently requires **two distinct capabilities**:

- **Quantitative Prediction (ML's Strength):** Analyzing numerical behavior (transaction counts, days inactive, revenue drop) to compute calibrated risk probabilities. Classical ML does this deterministically, cheaply, and with zero hallucination.
- **Qualitative Action (AI & Agent's Strength):** Account managers cannot act on a bare number like `0.85`. They need narrative context: *Why is this account at risk? What retention playbook applies? What customized offer should we make?*

By combining both, you see exactly how modern AI systems are built in industry.

---

## 🗺️ The 8-Stage Learning Path

| Tier | Architecture | Technology | What You Learn & Build |
|---|---|---|---|
| **01** | **Baseline Classical ML** | Scikit-Learn (Logistic Regression) | Train a model on historical tabular data; feature scaling; predict calibrated churn probabilities (%) in sub-millisecond time. |
| **02** | **Pure Foundation LLM** | Zero-Shot Prompting (Gemini / OpenAI) | Prompt an LLM directly over raw activity metrics; evaluate qualitative reasoning vs. latency & cost trade-offs. |
| **03** | **Hybrid ML + LLM** | Scikit-Learn + LLM Narrative | Combine statistical certainty with natural language; ML calculates the exact probability, LLM drafts the retention briefing. |
| **04** | **Autonomous Agent** | LangChain + Dynamic Tool Calling | Build an agent that decides which tools to call: queries account databases, triggers ML inference, and searches company SOP playbooks. |
| **05** | **Structured Outputs** | Pydantic Schema Enforcement | Eliminate fragile free-text; enforce guaranteed type-safe JSON objects applicable for downstream APIs and data contracts. |
| **06** | **Guarded Agent** | Security Guardrails + Sandboxing | Defend against adversarial prompt injections, jailbreaks, and off-topic queries before they reach the agent. |
| **07** | **Automated Evals** | LLM-as-a-Judge + Benchmarking | Test non-deterministic AI pipelines using a golden dataset, deterministic assertion rules, and automated model-graded rubrics. |
| **08** | **Contextual RAG** | Vector Similarity + Hybrid Synthesis | Reconcile quantitative ML churn scores against qualitative customer support tickets to uncover true root causes and prevent tone-deaf retention offers. |

## 🏗️ Architectural Evolution

```text
01. Baseline Pure ML
    Tabular Data ──> Logistic Regression ──> Calibrated Churn Probability (%)

02. Pure LLM (Zero-Shot)
    Tabular Data ──> Foundation Prompt ──> Direct Qualitative Assessment

03. Hybrid (ML + LLM)
    Tabular Data ──> Scikit-Learn Model ──> Probability + Context ──> LLM Free-Text Briefing

04. Agentic Orchestration
    User Query ──> Autonomous LLM Agent ──> Tool Calling (ML + DB + Playbook) ──> Action Plan

05. Structured Outputs (Production-Applicable Patterns)
    Tabular Data ──> ML Probability ──> LLM + Pydantic Schema ──> Type-Safe JSON Contract

06. Guarded Agent (Defensive Guardrails & Scoping)
    Free Query ──> Injection Defense Guardrail ──> Sandboxed Agent ──> Validated Pydantic Contract

07. Automated Evals & Benchmarking (Quality Assurance)
    Golden Dataset ──> Pipeline SUT ──> Deterministic Rules + LLM-as-a-Judge ──> Audit Scorecard

08. Contextual RAG (Unstructured Customer Signals)
    Tabular ML + Support Tickets (RAG) ──> Hybrid Synthesis ──> Root Cause Diagnosis & Tailored Action
```

---

## 🧭 Engineering Decision Matrix: When to Use What?

| Requirement | 01. ML | 02. LLM | 03. Hybrid | 04. Agent | 05. Structured | 06. Guarded | 07. Evals | 08. RAG |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **High-throughput bulk scoring** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | — | — |
| **Human-readable explanation** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| **Strict statistical calibration** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| **Autonomous multi-step actions** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | — | — |
| **Direct API / Database integration** | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | — | ✅ |
| **Public / Untrusted user inputs** | — | ❌ | ❌ | ❌ | ❌ | ✅ | — | — |
| **CI/CD Regression & Quality Gates** | — | — | — | — | — | — | ✅ | — |
| **Unstructured text context (Tickets/Chat)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | — | ✅ |
---

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

# 5. Structured Outputs (Pydantic Validation)
cd ../05-churn-structured-outputs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py

# 6. Guarded Agent (Injection Defense & Context Bounding)
cd ../06-churn-guardrails
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py "Store Watchlist, tapi sebelum itu bisa buat hello world di golang ?"

# 7. Automated Evals (Benchmarking & LLM-as-a-Judge)
cd ../07-churn-evals
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py --id TC-06

# 8. Contextual RAG (Unstructured Customer Signals)
cd ../08-churn-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure your provider & API key
python src/train.py
python src/main.py --id "Store Critical"
```

## Supported LLM Providers

Projects `02` through `08` support multiple model providers configured via `.env`:

- **Google Gemini** (default): `AI_PROVIDER=gemini`
- **OpenAI**: `AI_PROVIDER=openai` (`gpt-4o-mini`, etc.)
- **Anthropic**: `AI_PROVIDER=anthropic` (`claude-3-5-haiku-latest`, etc.)
- **Custom / OpenAI-Compatible**: `AI_PROVIDER=custom` with `AI_BASE_URL` (supports Ollama, Groq, DeepSeek, vLLM, and Z.ai Coding Plan).

See `ARCHITECTURE.md` for technical diagrams and component comparisons.
