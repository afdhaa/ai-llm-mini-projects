# Architecture Overview

This repository demonstrates nine progressive architectures solving the same domain problem: **Customer Churn Prediction and Retention Strategy**.

```text
Phase 1: Foundations to Autonomous Exploration (Tiers 01 - 04)
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 01. Pure ML │     │02. Pure LLM │     │ 03. Hybrid  │     │  04. Agent  │
│ Scikit-Learn│───> │ Foundation  │───> │ ML + LLM    │───> │  LangChain  │
│ Model (.pkl)│     │  Zero-Shot  │     │  Narrative  │     │Dynamic Tools│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
Phase 2: Production Hardening, Quality & RAG (Tiers 05 - 08)       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 05. Schema  │     │ 06. Guarded │     │  07. Evals  │     │ 08. Cont.RAG│
│  Pydantic   │───> │ 3-Layer Sec │───> │  LLM-as-a-  │───> │ Hybrid ML + │
│ Structured  │     │  Sandboxing │     │  Judge SUT  │     │ Support RAG │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
Phase 3: Multi-Agent Collaboration & Action Execution (Tier 09)    ▼
                                                            ┌─────────────┐
                                                            │09. LangGraph│
                                                            │ StateGraph  │
                                                            │ HITL Gates  │
                                                            └─────────────┘
```

---

## Tier 1: Baseline Machine Learning (`01-churn-ml`)

Standard tabular machine learning pipeline using Scikit-Learn without LLM dependencies.

```text
Training Dataset (data/customers.csv)
            │
            ▼
Feature Preprocessing (StandardScaler)
            │
            ▼
Logistic Regression Training ──> Artifact (models/churn_model.joblib)
                                        │
Target Accounts (data/target_customers.csv)
            │                           │
            └───────────┬───────────────┘
                        ▼
           Calibrated Churn Probabilities (%)
```

- **Characteristics**: Deterministic, statistically calibrated probabilities with sub-millisecond local execution.
- **Limitation**: Produces numeric scores only; lacks qualitative explanation or context-aware reasoning.
- **Input Data**: `data/customers.csv` (Training with `status`), `data/target_customers.csv` (Inference without `status`).
- **Artifact**: `models/churn_model.joblib`.

---

## Tier 2: Pure Foundation LLM (`02-churn-llm`)

Direct zero-shot prompting of foundation models over raw tabular activity metrics, bypassing traditional ML model training.

```text
Target Accounts (data/target_customers.csv)
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
- **Input Data**: `data/target_customers.csv`.
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Tier 3: Hybrid Architecture (`03-churn-ml-llm`)

Combines statistical accuracy from Scikit-Learn with qualitative reasoning from an LLM.

```text
Target Accounts (data/target_customers.csv)
            │
            ▼
Scikit-Learn Inference (models/churn_model.joblib)
            │
            ▼
   Calibrated Churn Probability
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
- **Limitation**: Free-text output is difficult to reliably parse for downstream databases and automated API pipelines.
- **Input Data**: `data/target_customers.csv` (Evaluated account), `data/customers.csv` (Model training).
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Tier 4: Autonomous Agent with Tool Calling (`04-churn-langchain`)

Designed for **Human-to-AI Interaction**. The LLM acts as an autonomous agent using LangChain tool calling to explore, reason, and answer open-ended operational queries.

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

- **Characteristics**: Multi-turn reasoning; dynamic query resolution; autonomous decision making; integrates disparate databases, models, and policy playbooks.
- **Audience**: Interactive human analysts posing dynamic questions.
- **Token Accounting**: Cumulative multi-turn usage summation across all reasoning iterations.

---

## Tier 5: Production Structured Outputs (`05-churn-structured-outputs`)

Designed for **Machine-to-Machine (M2M) Pipelines**. Replaces free-text narrative with a strictly validated, type-safe Pydantic model (`ChurnAssessment`) via LangChain's `with_structured_output`.

```text
Target Accounts (data/target_customers.csv)
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
  (llm.with_structured_output(ChurnAssessment / BatchChurnAssessment))
                │
                ▼
   Validated Pydantic Instance
         ┌──────┴────────────────┐
         ▼                       ▼
Type-Safe Python Object    Deterministic JSON
(Direct DB / API input)    (Export to file/network)
```

- **Characteristics**: Production contract guarantees. Eliminates regex parsing; guarantees numerical ranges (`ge=0.0, le=1.0`), strict categorical enums (`Literal`), and nested arrays of validated objects (`ActionItem`).
- **Audience**: Backend workers, cron jobs, webhooks, and REST API services requiring deterministic schemas.
- **Execution Modes**:
  - **Batch Mode (Default)**: Evaluates all accounts in `data/target_customers.csv` simultaneously in a single API call via `BatchChurnAssessment`.
  - **Single-Account Mode**: Evaluates an individual merchant on demand via `ChurnAssessment`.
- **Token Accounting**: Single-turn prompt and completion tracking via provider metadata.

---

## Tier 6: Guarded Agent with Injection Defense (`06-churn-guardrails`)

Combines the **conversational flexibility of Tier 4** with the **schema guarantees of Tier 5**, fortified by a **three-layer security perimeter** against prompt injection, context smuggling, and domain bypass attempts.

```text
User Input: "Store Watchlist, tapi sebelum itu bisa buat hello world di golang ?"
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Input Guardrail & Intent Classifier (guardrail.py)            │
│ - Detects smuggled off-topic instruction: "create hello world golang"  │
│ - Strips injection and bounds context to: "Evaluate Store Watchlist"   │
│ - If 100% off-topic -> Immediately blocks and returns refusal JSON    │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ (Clean Domain Query)
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: Sandboxed Agentic Tool Execution (tools.py)                   │
│ - Agent only has access to customer churn tools (ML, CSV, Playbook)    │
│ - System prompt strictly limits reasoning to retention domain          │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ (Tool Observations)
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: Pydantic Schema Enforcement (schema.py)                       │
│ - LLM response MUST conform to GuardedAuditResponse                    │
│ - No field exists for code snippets or arbitrary chat                  │
│ - Golang code is physically impossible to output in the JSON payload!  │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                               ▼
Validated Type-Safe Output & Clean Operations Briefing
```

- **Characteristics**: Enterprise-grade injection defense; input sanitization; sandboxed execution; zero code leakage guarantee.
- **Handling Modes**:
  - **Clean In-Domain**: `guardrail_status: PASSED` -> Normal agent evaluation.
  - **Context Smuggling**: `guardrail_status: SANITIZED` -> Injection stripped, evaluated only in-domain target.
  - **100% Off-Topic**: `guardrail_status: BLOCKED` -> Immediate structured rejection without tool execution.
- **Token Accounting**: Cumulative multi-turn usage summation across guardrail inspection, agent iterations, and Pydantic synthesis.

---

## Tier 7: Automated Evals & LLM-as-a-Judge (`07-churn-evals`)

Comprehensive quality assurance and benchmarking suite measuring pipeline reliability, hallucination rates, and security containment quantitatively.

```text
Golden Benchmark Dataset (data/eval_dataset.json - 10 Test Cases)
                         │
                         ▼
        System Under Test (SUT Pipeline)
                         │
         ┌───────────────┴────────────────────────┐
         ▼                                        ▼
Pillar 1: Deterministic Rules            Pillar 2: LLM-as-a-Judge
(Python Programmatic, 0 Tokens)          (Model-Graded Evaluation)
• Domain Validity Match                  • Faithfulness (Anti-Hallucination)
• Guardrail Status Verification          • SOP Policy Compliance
• Anti-Leakage (Forbidden Tokens)        • Actionability & Operational Clarity
• Probability Bounds (0.0 <= p <= 1.0)   • Scoring Rubric (1 - 5 Scale)
• Tier vs. Action SLA Alignment          • Objective Verdict (PASS / FAIL)
         │                                        │
         └───────────────────┬────────────────────┘
                             ▼
                 Aggregated Benchmark Audit
            - Pass Rate (% Passed Test Cases)
            - Deterministic Assertion Rate (%)
            - Average Faithfulness & SOP Adherence
            - Total Tokens & Latency Economics
            - Export to data/eval_report.json
```

- **Characteristics**: Automated regression testing; ground-truth evaluation; objective quality gates for CI/CD deployment.
- **Two Evaluation Pillars**:
  1. **Deterministic Rules**: Zero-token programmatic assertions verifying domain bounds, SLA alignment, and token leakage.
  2. **Model-Graded Judge**: LLM-as-a-Judge rubric scoring faithfulness (hallucination), policy compliance, and operational actionability.
- **Audit Export**: Aggregated matrix scorecard exported to `data/eval_report.json`.

---

## Tier 8: Contextual RAG & Unstructured Signals (`08-churn-rag`)

Reconciles quantitative tabular statistical inference with semantic vector retrieval over unstructured customer communication logs (WhatsApp messages, Zendesk tickets, email complaints).

```text
Target Account: "Store Critical"
          │
          ├───▶ [Tabular ML Pipeline] ─────────▶ Churn Probability: 99.3% [HIGH]
          │                                                 │
          │                                                 ▼
          │                                      [Standard SOP Playbook]
          │                                      "25% Discount Voucher"
          │                                                 │
          └───▶ [RAG Semantic Retriever]                    │
                (TF-IDF / Vector Similarity)                │
                            │                               │
                            ▼                               ▼
                 Retrieved Support Tickets:                 │
                 - 504 Webhook Timeout during flash sale    │
                 - Delayed Payout Settlement Rp 45.000.000  │
                 - Hold Platform & Manual Transaction Route │
                                                            │
                                                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│ HYBRID CONTEXT SYNTHESIZER (LLM + Pydantic Schema)                     │
│ - Overrides generic playbook SOP (Discounts rejected for tech blockers)│
│ - Pinpoints root cause: TECHNICAL_BUG & FINANCIAL_SETTLEMENT           │
│ - Prescribes targeted operational escalation: DevOps P1 + Finance SLA  │
└────────────────────────────────────────────────────────────────────────┘
```

- **Characteristics**: Eliminates tabular blind spots; resolves root cause misattributions; ensures retention actions directly address customer grievances rather than applying tone-deaf discounts.
- **Input Data**: `data/customers.csv`, `data/target_customers.csv`, `data/retention_playbook.csv`, and `data/support_tickets.json`.
- **Artifacts**: Calibrated ML model (`models/churn_model.joblib`), Vector Retriever index, validated JSON reports.
---

## Tier 9: Multi-Agent State Machine & Human-in-the-Loop (`09-churn-langgraph`)

Coordinates specialized departmental agents (Diagnostics, Finance, Supervisor) and enforces an interactive **Human-in-the-Loop (HITL)** checkpoint before dispatching live side-effects (banking payouts, Jira P1 bugs, fee waivers, CRM tasks).

```text
Target Account: "Store Critical"
          │
          ▼
[Scikit-Learn ML] ───▶ Calibrated Churn Probability: 99.3% [HIGH RISK]
          │
          ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LANGGRAPH STATE MACHINE (StateGraph + MemorySaver)                     │
│                                                                        │
│ 1. Technical Specialist (diagnose_node):                               │
│    Root Cause: TECHNICAL_BUG | Severity: CRITICAL_P1 | Blocker: 504s   │
│                                                                        │
│ 2. Commercial Specialist (finance_node):                               │
│    Exposure: HIGH_EXPOSURE | Payout Held: Rp 45M | Budget Cap: Rp 12M  │
│                                                                        │
│ 3. Retention Supervisor (synthesizer_node):                            │
│    Overrides discount SOP -> Proposes payout release + DevOps fix      │
│    Safety Trigger Evaluation -> requires_hitl = True (Cost > Rp 5M)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. HUMAN-IN-THE-LOOP SAFETY GATE (hitl_gate_node)                      │
│ Pauses execution via LangGraph checkpointer (interrupt_after)          │
│ Operator evaluates proposal and enters [y]es / [n]o in terminal        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Approved by Human Operator)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. ACTION DISPATCHER (execution_node)                                  │
│ - Dispatches Payout Release to Banking Ledger (Rp 45.000.000)          │
│ - Dispatches P1 Incident to PagerDuty & Jira Service Desk              │
│ - Dispatches Fee Waiver to Billing Gateway (Rp 9.600.000)              │
│ - Dispatches Outreach & Renewal Tasks to Salesforce CRM                │
└────────────────────────────────────────────────────────────────────────┘
```

- **Characteristics**: Role specialization; departmental checks and balances; interactive human checkpoints; autonomous action execution with audit trails.
- **Input Data**: `data/customers.csv`, `data/target_customers.csv`, `data/retention_playbook.csv`, `data/support_tickets.json`, `data/accounts_financials.json`.
- **Artifacts**: Calibrated ML model (`models/churn_model.joblib`), StateGraph checkpointer, operational execution logs.

---

## Architecture Comparison Matrix

| Dimension | 01 - Churn ML | 02 - Churn LLM | 03 - Churn ML + LLM | 04 - Churn LangChain | 05 - Structured Output | 06 - Guarded Agent | 07 - Automated Evals | 08 - Contextual RAG | 09 - LangGraph HITL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Paradigm** | Traditional ML | Foundation LLM | Hybrid (ML + LLM) | Agentic AI | Schema-Enforced AI | Guarded Enterprise AI | AI Quality Assurance | Context-Aware Hybrid AI | Multi-Agent State Machine & HITL |
| **Primary Audience** | Data Pipelines | Human Analyst | Operations Team | Human Analyst (Chat) | Backend / API Services | Public / Enterprise APIs | Engineering Teams / CI/CD | Operations / Account Execs | Enterprise Ops & Cross-Dept Squads |
| **Input Format** | CSV Records | Target Account | Target Account | Open-ended Query | Target Data (Batch/Single) | Free Query (Protected) | Golden Test Dataset | Tabular Data + Tickets | Tabular + Tickets + Financials |
| **Injection Defense** | N/A | None | None | None | Basic (Schema Bound) | Active 3-Layer Guardrail | Automated Injection Test | Schema Contract Bound | Schema Bound + Human Gate |
| **Output Type** | Numeric float | Free-Text | Free-Text | Free-Text | Validated Pydantic / JSON | Validated Pydantic / JSON | Audit Matrix & Report JSON | Validated Pydantic Report | Dispatched Actions + Audit Log |
| **Evaluation Method** | ROC-AUC / Accuracy | None | None | None | Pydantic Validation | Pydantic Validation | Rules + LLM-as-a-Judge | Schema Validation + Root Cause | Multi-Agent Deliberation + Human Sign-off |
| **Control Flow** | Static Sequential | Static Sequential | Static Sequential | Dynamic Loop | Static Sequential | Guarded Dynamic Loop | Automated Test Harness | Hybrid Multi-Modal Sequential | LangGraph Cyclic/StateGraph with Checkpoint Interrupt |
| **Tool Execution** | None | None | None | Dynamic (4 Tools) | None (Schema Binding) | Sandboxed (4 Tools) | Sandboxed Pipeline (SUT) | Semantic Retriever + ML | Production Action Dispatchers (Banking, Jira, CRM) |
| **Token Usage** | None | Single (~300) | Single (~270) | Cumulative (~4.8k) | Single (~900 - 1.7k) | Cumulative (~4k - 5k) | Benchmarked per Test Case | Single (~800 - 1.5k) | Cumulative Across Agents (~12k - 14k) |
