# 08 - Churn RAG (Hybrid Tabular ML + Unstructured Customer Signals)

> **Context-Aware Retention Architecture combining Scikit-Learn statistical inference with Semantic Vector Retrieval (RAG) over unstructured customer support tickets and communication logs.**

---

## 🎯 The Core Problem: Why Tabular ML Has Blind Spots

In Tiers `01` through `07`, our models evaluated accounts based strictly on **quantitative tabular metrics** (`transactions`, `active_days`, `inactive_days`):

* **Scikit-Learn Model Output:** `Store Critical` has a **99.3% Churn Probability (HIGH RISK)**.
* **Standard SOP Playbook Action:** *"Provide 25% discount voucher + 1 month waived platform fee; assign Senior Account Manager."*

### The Tone-Deaf Playbook Pitfall
If you only look at numbers, offering a **25% discount voucher** seems like a generous retention incentive. But what if the merchant's real problem is:
1. *"Webhook payment 504 gateway timeout during flash sales causing customer orders to hang"*?
2. *"Payout settlement of Rp 45.000.000 delayed for over 4 days"*?
3. Or worse: *"Store is shutting down retail operations due to corporate liquidation"*?

> **Offering a discount voucher to a merchant whose payments are broken will not prevent churn—it accelerates frustration and damages trust.**

`08-churn-rag` solves this by introducing **Retrieval-Augmented Generation (RAG)** over unstructured communication history (WhatsApp messages, Zendesk tickets, email complaints) to diagnose the **true root cause** before deciding the intervention.

---

## 🏗️ Architecture & Pipeline Flow

```text
Target Account: "Store Critical"
          │
          ├───▶ [1. Tabular ML Model] ─────────▶ Churn Probability: 99.3% [HIGH]
          │     (Scikit-Learn Pipeline)                     │
          │                                                 ▼
          │                                      [Standard SOP Playbook]
          │                                      "25% Discount Voucher"
          │                                                 │
          └───▶ [2. RAG Semantic Retriever]                 │
                (TF-IDF / Vector Similarity)                │
                            │                               │
                            ▼                               ▼
                 Retrieved Support Tickets:                 │
                 - Ticket #1031: 504 Webhook Timeout        │
                 - Ticket #1032: Payout Tertahan Rp 45jt    │
                 - Ticket #1033: Hold Checkout Platform     │
                                                            │
                                                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. HYBRID CONTEXT SYNTHESIZER (LLM + Pydantic Schema)                  │
│ Reconciles quantitative risk against qualitative ticket history        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. CONTEXT-AWARE RETENTION INTERVENTION (Type-Safe Output)             │
│ • Root Cause: TECHNICAL_BUG (Webhook failure & payout delay)           │
│ • SOP Status: OVERRIDE REQUIRED (Discounts are ineffective)            │
│ • Tailored Action:                                                     │
│   1. Priority 1 DevOps escalation for webhook fix (< 4 hrs)            │
│   2. Manual finance clearance for Rp 45.000.000 payout (< 6 hrs)       │
│   3. SLA incident post-mortem with financial credit waiver             │
│ • Owner: Technical Account Manager & Lead DevOps                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Account Intelligence Comparison Matrix

Here is how RAG context transforms retention decisions across target merchant accounts:

| Customer | ML Churn Prob | Generic Playbook SOP | Unstructured Ticket Signals (RAG) | Synthesized Root Cause & Tailored Action |
|---|:---:|---|---|---|
| **`Store Safe`** | **1.6%** (NO RISK) | Champion Partner Status | Routine inquiries: monthly tax invoice consolidation and POS cashier roles. | **`GENERAL_SATISFIED`**<br>Routine CRM partner loyalty perks; check-in for upcoming outlet expansion. |
| **`Store Stable`** | **29.2%** (LOW) | Loyalty points booster | Merchant asking about shipping subsidies for campaign 10.10 & instant courier activation. | **`GENERAL_SATISFIED`**<br>Maintain standard CRM support; activate requested instant courier integration. |
| **`Store Watchlist`** | **56.8%** (MEDIUM) | Subsidized shipping vouchers (3 orders) | Objection to platform fee increase from 1.5% to 2.2%; citing competitor offer at 1.2% MDR. | **`PRICING_COMMERCIAL`**<br>Override generic vouchers; schedule commercial renegotiation proposing volume-tiered MDR. |
| **`Store Critical`** | **99.3%** (HIGH) | 25% discount voucher + waived platform fee | Severe 504 webhook timeouts during flash sale + Rp 45.000.000 payout settlement delayed. | **`TECHNICAL_BUG`**<br>Standard voucher rejected. Urgent P1 DevOps escalation and expedited finance clearance. |
| **`Store Inactive`** | **99.6%** (HIGH) | 25% discount voucher + waived platform fee | Formal notice of complete business closure and liquidation. | **`ACCOUNT_LIFECYCLE`**<br>Voucher rejected. Churn non-preventable. Halt marketing campaigns and expedite account closure. |

---

## 🚀 Setup & Execution

### 1. Environment Setup

```bash
cd 08-churn-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your provider API key (optional for heuristic mode)
```

### 2. Train Tabular ML Model

Train the Scikit-Learn Logistic Regression model on historical customer data:

```bash
python src/train.py
# Output: Model trained: models/churn_model.joblib
```

### 3. Run Single Merchant Evaluation

Evaluate `Store Critical` (the prime contrasting example):

```bash
python src/main.py --id "Store Critical"
```

Or evaluate other accounts:

```bash
python src/main.py --id "Store Watchlist"
python src/main.py --id "Store Inactive"
```

### 4. Run Batch Evaluation & Export JSON

Process all accounts simultaneously and export a validated Pydantic JSON report:

```bash
python src/main.py --id all -o data/retention_plan_output.json
```

---

## 🛡️ Production-Applicable Engineering Patterns

1. **Lightweight In-Memory Semantic Indexing:** Uses Scikit-Learn vectorization with cosine similarity for fast, deterministic, zero-external-dependency retrieval across support tickets.
2. **Strict Type-Safe Contracts (`schema.py`):** Uses Pydantic to ensure all root cause categories, sentiment tags, and override decisions conform to strict data contracts.
3. **Resilient Dual-Mode Execution:** Operates seamlessly with live foundation models (Gemini, OpenAI, Anthropic, Custom LLMs) and falls back to deterministic heuristic synthesis for offline CI/CD test environments.
4. **Externalized Heuristic Lexicon (`data/sentiment_rules.json`):** Decouples sentiment keywords and priority tiers from Python logic into a JSON configuration file, enabling domain teams to update vocabulary without touching code.
