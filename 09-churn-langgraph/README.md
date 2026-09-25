# 09 - Churn LangGraph (Multi-Agent State Machine & Human-in-the-Loop)

> **Enterprise-Grade Retention Orchestration combining Scikit-Learn tabular inference with a LangGraph Multi-Agent State Machine and Human-in-the-Loop (HITL) safety gates before dispatching operational side-effects.**

---

## 🎯 The Core Problem: The Danger of Autonomous Side-Effects

In Tiers `01` through `08`, all architectures produced **passive recommendations** (free-text briefings or structured JSON documents). They diagnosed issues and suggested playbooks, but never executed real actions in external enterprise systems.

In real-world SaaS, FinTech, and e-commerce platforms, account retention cannot remain a passive document. It requires **active operational interventions**:
1. Unfreezing held settlement payouts in the Core Banking Ledger.
2. Opening P1 emergency incident tickets in PagerDuty & Jira Service Desk.
3. Applying financial fee waivers and billing credits in Stripe / Billing Gateways.
4. Logging priority commercial contract renegotiations in Salesforce CRM.

### Why Monolithic LLMs Fail in Enterprise Operations
If a single, autonomous LLM agent is given direct permission to trigger these tools:
- **Hallucinated Financial Liabilities:** An agent might authorize an unvetted Rp 45.000.000 payout release or 50% lifetime fee discount without verifying company margin or fraud flags.
- **Departmental Blind Spots:** A single prompt cannot effectively balance conflicting departmental priorities. Tech support wants to solve bugs at any cost; Finance wants to protect unit economics; Customer Success wants to appease the merchant.
- **No Safety Checkpoint:** Once an action is dispatched to production APIs (banking, billing, PagerDuty), the blast radius is irreversible.

`09-churn-langgraph` solves this by introducing a **Multi-Agent State Machine** orchestrated via **LangGraph**, where specialized agents deliberate across distinct domains, and high-impact actions are held at an interactive **Human-in-the-Loop (HITL) Safety Checkpoint** before execution.

---

## 🏗️ Multi-Agent Architecture & State Flow

```text
Target Account (e.g., "Store Critical")
          │
          ▼
[Tabular ML Model] ───▶ Calibrated Churn Probability (%) [e.g. 99.3% HIGH RISK]
          │
          ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LANGGRAPH STATE MACHINE (StateGraph with MemorySaver Checkpointer)     │
│                                                                        │
│   1. Technical & Diagnostics Specialist (diagnose_node)                │
│      • Analyzes ML metrics + unstructured support tickets              │
│      • Uncovers root cause: TECHNICAL_BUG (504 webhook timeouts)       │
│      • Sets severity: CRITICAL_P1 | Flags DevOps escalation: MANDATORY │
│                                                                        │
│   2. Commercial & Finance Specialist (finance_node)                    │
│      • Evaluates GMV (Rp 320M), platform revenue, and merchant margin  │
│      • Sets strict incentive budget ceiling: Rp 12.000.000 (cap)       │
│      • Assesses pending payout hold: Rp 45.000.000 (unfreeze verified) │
│                                                                        │
│   3. Retention Lead / Supervisor (synthesizer_node)                    │
│      • Overrides generic discount SOP (discounts damage trust for bugs)│
│      • Harmonizes Tech & Finance into a concrete RetentionProposal     │
│      • Calculates total financial impact: Rp 57.000.000                │
│      • Evaluates Safety Policy -> requires_hitl = True                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. HUMAN-IN-THE-LOOP (HITL) SAFETY GATE (hitl_gate_node)               │
│ • State pauses execution via LangGraph checkpoint (interrupt_after)    │
│ • Condition: Total Cost > Rp 5M  OR  Churn > 80%  OR  P1 / Payout Hold │
│                                                                        │
│   [OPERATOR DECISION IN TERMINAL / CLI]:                               │
│   [y] Approve  ──▶ Graph Resumes with hitl_status = "APPROVED"         │
│   [n] Reject   ──▶ Graph Resumes with hitl_status = "REJECTED"         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. OPERATIONAL ACTION DISPATCHER (execution_node)                      │
│ • If APPROVED / AUTO_APPROVED:                                         │
│   - Fintech Settlement Engine  ──▶ Unfreeze Rp 45.000.000 payout       │
│   - PagerDuty & Jira           ──▶ Dispatch P1 DevOps Incident         │
│   - Billing & Subscriptions    ──▶ Apply 1.5-month fee waiver          │
│   - Salesforce Enterprise CRM  ──▶ Log executive contract renewal      │
│ • If REJECTED:                                                         │
│   - Blocks all external side-effects; logs CANCELLED_BY_HUMAN audit    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 👥 The 3 Specialist Agents

| Agent / Node | Primary Responsibility | Input Context | Output Schema |
|---|---|---|---|
| **Technical Specialist** (`diagnose_node`) | Pinpoints root cause, technical blockers, and engineering severity. | Tabular ML Churn %, Activity days, Support Tickets | `DiagnosticFindings` |
| **Commercial Specialist** (`finance_node`) | Evaluates business exposure, merchant LTV, payout balances, and enforces budget caps. | Merchant Financials (GMV, Revenue, Margin), ML Risk | `FinancialAssessment` |
| **Retention Supervisor** (`synthesizer_node`) | Harmonizes conflicting priorities, overrides generic SOPs, and determines HITL triggers. | Diagnostics findings, Financial report, Baseline SOP | `RetentionProposal` |

---

## 🛡️ The HITL Safety Policy

Not every retention action needs to burden human operators. The supervisor evaluates the safety policy:

- **Automatic Approval (`AUTO_APPROVED`):**
  - Total proposed financial cost $\le \text{Rp } 5.000.000$.
  - Churn risk is `LOW` or `MEDIUM` ($< 80\%$).
  - No Core Banking payout releases or P1 DevOps emergencies.
  - *Example:* **`Store Watchlist`** (Interim 1.8% rate hold valued at Rp 760.000 + CRM check-in).

- **Human Review Required (`PENDING_REVIEW`):**
  - Total financial value $> \text{Rp } 5.000.000$.
  - Churn risk $\ge 80\%$ (`HIGH RISK`).
  - Plan contains high-liability side-effects (`FINANCE_PAYOUT_RELEASE` or `DEVOPS_INCIDENT`).
  - *Example:* **`Store Critical`** (P1 Webhook bug, Rp 45.000.000 payout release, Rp 9.600.000 fee waiver).

---

## 📊 Account Intelligence & Strategy Contrast

| Customer | ML Churn Prob | Diagnostic Root Cause | Financial Exposure & Budget Cap | Supervisor Retention Plan | HITL Gate Status |
|---|:---:|---|---|---|:---:|
| **`Store Watchlist`** | **56.8%** (MEDIUM) | `PRICING_COMMERCIAL`<br>Protesting fee hike from 1.5% to 2.2% vs competitor 1.2% MDR. | **Moderate Exposure**<br>GMV Rp 95M. Cap: Rp 2.450.000. | Interim 1.8% rate hold for 2 months (Cost: Rp 760K) + Pricing Committee review. | **`AUTO_APPROVED`**<br>(Low cost, standard commercial lever) |
| **`Store Critical`** | **99.3%** (HIGH) | `TECHNICAL_BUG`<br>Webhook 504 timeouts during flash sale + Rp 45M payout hold. | **High Exposure**<br>GMV Rp 320M. Held: Rp 45M. Cap: Rp 12.000.000. | Emergency P1 DevOps incident + Same-day Rp 45M payout release + 1.5-month fee waiver (Rp 9.6M). | **`PENDING_REVIEW`**<br>(High cost, P1 bug & banking payout release) |

---

## 🚀 Setup & Execution

### 1. Environment Setup

Create a dedicated virtual environment and install dependencies:

```bash
cd 09-churn-langgraph
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)

Configure your preferred LLM provider in `.env`. Supported providers: `custom` (Z.ai / Ollama / DeepSeek), `gemini`, `openai`, or `anthropic`:

```env
AI_PROVIDER=custom
AI_BASE_URL=https://api.z.ai/api/coding/paas/v4
AI_API_KEY=your_z_ai_api_key_here
AI_MODEL=GLM-5.3-Flash
```

### 3. Train Baseline Machine Learning Model

Train the Scikit-Learn logistic regression model:

```bash
python src/train.py
# Output: Model trained successfully: models/churn_model.joblib
```

### 4. Run Multi-Agent Retention Pipeline

#### Interactive Human-in-the-Loop Mode (Default)
Evaluate a high-risk account. The pipeline streams multi-agent deliberation in real time, displays findings, pauses at the checkpoint, and presents a 4-option operational menu:

```bash
python src/main.py --id "Store Critical"
```

Interactive Control Menu:
```text
  ╭──────────────────────────────────────────────────────────────────────────╮
  │ HUMAN-IN-THE-LOOP (HITL) OPERATIONAL CONTROL MENU                        │
  ├──────────────────────────────────────────────────────────────────────────┤
  │ [1] ✅ Approve All Actions & Dispatch to Target Systems                  │
  │ [2] 🔍 Interactive Item-by-Item Review (Toggle specific actions)         │
  │ [3] 💬 Steer / Revise Plan (Send guidance to Supervisor Agent to revise) │
  │ [4] ❌ Reject Proposal Entirely (Block all side-effects)                 │
  ╰──────────────────────────────────────────────────────────────────────────╯
  Select action [1/2/3/4] (default: 1):
```

- **Option `[1]` (Approve All):** Immediately authorizes all synthesized actions.
- **Option `[2]` (Item-by-Item Review):** Prompts `[y/n]` per individual action. Approved items are dispatched; unapproved items are omitted and marked as `SKIPPED`.
- **Option `[3]` (Steer / Revise Plan):** Enter custom feedback (e.g. *"Batalkan diskon, fokus ke P1 DevOps dan unfreeze payout"*). The Supervisor agent immediately regenerates a revised proposal based on your directives and returns to the menu for confirmation.
- **Option `[4]` (Reject All):** Cancels all actions and records a `CANCELLED_BY_HUMAN` blocked audit entry.

#### Automated CI / Batch Mode (`--auto-approve`)
Bypass the interactive menu for automated pipelines:

```bash
python src/main.py --id "Store Critical" --auto-approve
```

#### Human Rejection Simulation (`--reject`)
Simulate human operator declining high-risk actions via flag:

```bash
python src/main.py --id "Store Critical" --reject --feedback "CFO denied payout release pending reconciliation."
```

#### Auto-Approved Account Evaluation
Evaluate an account whose action plan is within low-risk limits:

```bash
python src/main.py --id "Store Watchlist"
```
*(The graph evaluates the proposal, recognizes that cost is under Rp 5M and risk is moderate, and automatically dispatches side-effects without prompting the operator).*
---

## 📈 Token Accounting & Performance

Each specialist node tracks its individual prompt and completion tokens. The final audit output displays cumulative token usage across the multi-agent deliberation:

```text
--------------------------------------------------------------------------------
  [7] MULTI-AGENT TOKEN ECONOMICS & PIPELINE RESOURCE USAGE
      • Diagnostic Specialist Tokens : Prompt + Completion Tracked
      • Financial Specialist Tokens  : Prompt + Completion Tracked
      • Retention Supervisor Tokens  : Prompt + Completion Tracked
      • Cumulative Token Usage       : 13,172 tokens (3,980 prompt, 9,192 completion)
================================================================================
```
