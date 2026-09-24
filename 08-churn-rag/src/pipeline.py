import json
import os
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from dotenv import load_dotenv

from rag import TicketRetriever
from schema import (
    ChurnRagReport,
    ContextAwareIntervention,
    RootCauseCategory,
    SopBaselineAction,
    TicketEvidence,
    TokenUsage,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def extract_token_usage(raw_msg) -> TokenUsage:
    """Extract prompt, completion, and total tokens from raw response."""
    p, c, t = 0, 0, 0
    if raw_msg and hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
        p = raw_msg.usage_metadata.get("input_tokens", 0) or 0
        c = raw_msg.usage_metadata.get("output_tokens", 0) or 0
        t = raw_msg.usage_metadata.get("total_tokens", 0) or (p + c)
    elif raw_msg and hasattr(raw_msg, "response_metadata") and raw_msg.response_metadata:
        u = raw_msg.response_metadata.get("token_usage") or raw_msg.response_metadata.get("usage") or {}
        p = u.get("prompt_tokens") or u.get("input_tokens", 0) or 0
        c = u.get("completion_tokens") or u.get("output_tokens", 0) or 0
        t = p + c
    return TokenUsage(prompt_tokens=int(p), completion_tokens=int(c), total_tokens=int(t))



class ChurnRagPipeline:
    """End-to-End Orchestrator: Tabular ML + SOP Playbook + RAG Support Tickets + LLM Synthesis."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        playbook_path: Path | str | None = None,
        tickets_path: Path | str | None = None,
        sentiment_rules_path: Path | str | None = None,
        llm=None,
    ):
        self.root = ROOT
        self.model_path = Path(model_path or (self.root / "models" / "churn_model.joblib"))
        self.playbook_path = Path(playbook_path or (self.root / "data" / "retention_playbook.csv"))
        self.sentiment_rules_path = Path(sentiment_rules_path or (self.root / "data" / "sentiment_rules.json"))
        self.retriever = TicketRetriever(tickets_path)
        self.llm = llm
        self.model = self._load_model()
        self.playbook_df = self._load_playbook()
        self.sentiment_rules = self._load_sentiment_rules()
    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found at '{self.model_path}'. Run: python src/train.py first."
            )
        return joblib.load(self.model_path)

    def _load_playbook(self) -> pd.DataFrame:
        if not self.playbook_path.exists():
            raise FileNotFoundError(f"Playbook file not found at '{self.playbook_path}'.")
        return pd.read_csv(self.playbook_path)

    def _load_sentiment_rules(self) -> list[dict[str, Any]]:
        """Load configurable sentiment rules from JSON lexicon."""
        if self.sentiment_rules_path.exists():
            try:
                with open(self.sentiment_rules_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                    return sorted(rules, key=lambda r: r.get("priority", 99))
            except Exception as e:
                print(f"[WARN] Failed to load sentiment rules from {self.sentiment_rules_path}: {e}")
        return []

    def classify_sentiment(self, subject: str, message: str) -> tuple[str, str]:
        """Classify ticket sentiment dynamically using loaded JSON rules."""
        combined_text = f"{subject} {message}".lower()
        for rule in self.sentiment_rules:
            keywords = rule.get("keywords", [])
            if any(k.lower() in combined_text for k in keywords):
                return rule.get("sentiment", "CONCERNED"), rule.get("description", "Rule match")
        return "POSITIVE", "Standard routine operational communication with no grievance detected."

    def predict_tabular(self, customer_data: dict[str, Any]) -> tuple[float, str]:
        """Compute calibrated probability from Scikit-Learn model and map to risk tier."""
        features = ["transactions", "active_days", "inactive_days"]
        input_df = pd.DataFrame([customer_data])[features]
        ml_prob = float(self.model.predict_proba(input_df)[0][1])

        if ml_prob >= 0.70:
            risk_tier = "HIGH"
        elif ml_prob >= 0.40:
            risk_tier = "MEDIUM"
        elif ml_prob >= 0.10:
            risk_tier = "LOW"
        else:
            risk_tier = "NO RISK"

        return ml_prob, risk_tier

    def get_sop_baseline(self, risk_level: str) -> SopBaselineAction:
        """Fetch procedural retention baseline from standard SOP playbook."""
        matched = self.playbook_df[self.playbook_df["risk_level"].str.upper() == risk_level.upper()]
        if matched.empty:
            return SopBaselineAction(
                risk_level=risk_level,
                sla="Standard Cadence",
                pic="Automated CRM",
                generic_incentive="None",
                generic_actions=["Monitor usage"],
            )

        row = matched.iloc[0]
        raw_actions = str(row.get("actions", "")).split(";")
        cleaned_actions = [a.strip() for a in raw_actions if a.strip()]

        return SopBaselineAction(
            risk_level=str(row["risk_level"]),
            sla=str(row.get("sla", "Standard")),
            pic=str(row.get("pic", "Customer Success")),
            generic_incentive=str(row.get("incentive", "-")),
            generic_actions=cleaned_actions,
        )

    def synthesize(
        self,
        customer_data: dict[str, Any],
        focus_query: str = "churn risk complaint technical issue pricing cancellation",
    ) -> ChurnRagReport:
        """Execute full hybrid synthesis combining ML, Playbook, RAG, and LLM reasoning."""
        customer_name = customer_data["customer"]
        ml_prob, risk_level = self.predict_tabular(customer_data)
        sop_baseline = self.get_sop_baseline(risk_level)

        # Retrieve customer support tickets via RAG
        raw_tickets = self.retriever.retrieve_context(customer_name, focus_query=focus_query, top_k=5)

        # Synthesize via LLM
        if self.llm is not None:
            intervention, tickets_evidence, token_usage = self._synthesize_with_llm(
                customer_data, ml_prob, risk_level, sop_baseline, raw_tickets
            )
        else:
            intervention, tickets_evidence, token_usage = self._offline_heuristic_synthesis(
                customer_data, ml_prob, risk_level, sop_baseline, raw_tickets
            )

        return ChurnRagReport(
            customer=customer_name,
            transactions=int(customer_data["transactions"]),
            active_days=int(customer_data["active_days"]),
            inactive_days=int(customer_data["inactive_days"]),
            churn_probability=round(ml_prob, 4),
            ml_risk_level=risk_level,
            sop_baseline=sop_baseline,
            retrieved_tickets=tickets_evidence,
            tailored_intervention=intervention,
            token_usage=token_usage,
        )

    def _synthesize_with_llm(
        self,
        customer_data: dict[str, Any],
        ml_prob: float,
        risk_level: str,
        sop_baseline: SopBaselineAction,
        raw_tickets: list[dict[str, Any]],
    ) -> tuple[ContextAwareIntervention, list[TicketEvidence], TokenUsage]:
        """Use LangChain ChatModel with structured output to synthesize root cause and tailored action."""
        tickets_text = ""
        tickets_evidence: list[TicketEvidence] = []

        if raw_tickets:
            for t in raw_tickets:
                tickets_text += (
                    f"- Ticket #{t.get('ticket_id')}: [{t.get('channel')}] {t.get('timestamp')}\n"
                    f"  Subject: {t.get('subject')}\n"
                    f"  Message: {t.get('message')}\n"
                    f"  Category: {t.get('category')} | Status: {t.get('status')}\n\n"
                )
                tickets_evidence.append(
                    TicketEvidence(
                        ticket_id=t.get("ticket_id", "N/A"),
                        channel=t.get("channel", "N/A"),
                        timestamp=t.get("timestamp", "N/A"),
                        snippet=f"[{t.get('subject')}] {t.get('message')[:120]}...",
                        sentiment=self.classify_sentiment(t.get("subject", ""), t.get("message", ""))[0],
                        sentiment_reason=self.classify_sentiment(t.get("subject", ""), t.get("message", ""))[1],
                    )
                )
        else:
            tickets_text = "No recent support tickets or complaints recorded on file."

        prompt = f"""You are an Expert Customer Retention & Churn Architect.
Your task is to analyze a merchant account by reconciling quantitative ML risk scores with qualitative support ticket history retrieved via RAG.

ACCOUNT QUANTITATIVE METRICS (Tabular ML):
- Merchant: {customer_data['customer']}
- Monthly Transactions: {customer_data['transactions']}
- Active Days: {customer_data['active_days']}
- Inactive Days: {customer_data['inactive_days']}
- ML Churn Probability: {ml_prob:.1%} ({risk_level} RISK)

DEFAULT SOP RETENTION PLAYBOOK (Without Context):
- Standard PIC: {sop_baseline.pic}
- Standard SLA: {sop_baseline.sla}
- Generic Incentive: {sop_baseline.generic_incentive}
- Generic Actions: {'; '.join(sop_baseline.generic_actions)}

RETRIEVED UNSTRUCTURED SUPPORT TICKETS (RAG Context):
{tickets_text}

CRITICAL REASONING INSTRUCTIONS:
1. Examine if the merchant's real problem is reflected in the support tickets.
2. Determine if the default SOP incentive (e.g. discount voucher) solves their actual problem, or if it is tone-deaf/inadequate.
   - Example: If a merchant is blocked by 504 webhook timeouts or payout delays, a 25% discount voucher does NOT help and will alienate them.
   - Example: If a merchant is shutting down their business, retention offers are moot; focus on orderly offboarding.
3. Categorize the true primary_root_cause using RootCauseCategory enum.
4. Formulate specific, context-aware tailored_action_items with an assigned responsible role (recommended_pic) and urgency.
5. In 'ticket_evaluations', assess EACH retrieved support ticket: fill ticket_id, channel, timestamp, snippet, sentiment, and sentiment_reason explaining why the merchant feels this way.
"""

        try:
            structured_llm = self.llm.with_structured_output(ContextAwareIntervention, include_raw=True)
            raw_response = structured_llm.invoke(prompt)
            intervention = raw_response["parsed"]
            if intervention is None:
                raise ValueError("Structured LLM returned None or failed to parse response.")
            if isinstance(intervention, dict):
                intervention = ContextAwareIntervention(**intervention)
            if intervention.ticket_evaluations:
                tickets_evidence = intervention.ticket_evaluations
            token_usage = extract_token_usage(raw_response.get("raw"))
            return intervention, tickets_evidence, token_usage
        except Exception as e:
            print(f"[WARN] Structured LLM invocation failed ({e}), falling back to heuristic synthesis.")
            return self._offline_heuristic_synthesis(
                customer_data, ml_prob, risk_level, sop_baseline, raw_tickets
            )

    def _offline_heuristic_synthesis(
        self,
        customer_data: dict[str, Any],
        ml_prob: float,
        risk_level: str,
        sop_baseline: SopBaselineAction,
        raw_tickets: list[dict[str, Any]],
    ) -> tuple[ContextAwareIntervention, list[TicketEvidence], TokenUsage]:
        """Deterministic offline fallback synthesis for smoke tests and non-LLM environments."""
        tickets_evidence: list[TicketEvidence] = []
        customer = customer_data["customer"].lower()

        # Build evidence
        for t in raw_tickets:
            sentiment, reason = self.classify_sentiment(t.get("subject", ""), t.get("message", ""))
            tickets_evidence.append(
                TicketEvidence(
                    ticket_id=t.get("ticket_id", "N/A"),
                    channel=t.get("channel", "N/A"),
                    timestamp=t.get("timestamp", "N/A"),
                    snippet=f"[{t.get('subject', '')}] {t.get('message', '')[:120]}...",
                    sentiment=sentiment,
                    sentiment_reason=reason,
                )
            )
        if "critical" in customer:
            intervention = ContextAwareIntervention(
                primary_root_cause=RootCauseCategory.TECHNICAL_BUG,
                root_cause_explanation=(
                    "Merchant experienced repeated webhook 504 gateway timeouts during flash sale, "
                    "followed by unresolved payout settlement delays of Rp 45.000.000, forcing manual transaction rerouting."
                ),
                is_sop_adequate=False,
                override_justification=(
                    "Standard 25% discount voucher rejected. The churn driver is severe technical and settlement "
                    "friction, not price sensitivity. Offering discounts while payments fail aggravates merchant distrust."
                ),
                tailored_action_items=[
                    "Escalate webhook 504 timeouts to DevOps/Engineering with Priority 1 SLA (< 4 hours).",
                    "Coordinate manual finance settlement clearance for pending Rp 45.000.000 payout within 6 hours.",
                    "Provide technical incident post-mortem with financial SLA credit waiver rather than promotional vouchers.",
                ],
                recommended_pic="Technical Account Manager & Lead DevOps",
                urgency="CRITICAL_IMMEDIATE",
            )
        elif "watchlist" in customer:
            intervention = ContextAwareIntervention(
                primary_root_cause=RootCauseCategory.PRICING_COMMERCIAL,
                root_cause_explanation=(
                    "Merchant objected to recent platform fee hike from 1.5% to 2.2% per transaction, citing competitor "
                    "offers at 1.2% MDR and threatening platform migration."
                ),
                is_sop_adequate=True,
                override_justification=(
                    "Standard commercial intervention is applicable, but should be tailored toward custom volume-tiered MDR "
                    "rather than temporary shipping vouchers."
                ),
                tailored_action_items=[
                    "Schedule commercial renegotiation session proposing tiered MDR (1.4% at target volume threshold).",
                    "Present benchmark report demonstrating platform GMV conversion uplift vs competitor.",
                    "Extend 60-day promotional rate freeze pending quarterly volume review.",
                ],
                recommended_pic="Senior Commercial / Partnerships Manager",
                urgency="HIGH",
            )
        elif "inactive" in customer:
            intervention = ContextAwareIntervention(
                primary_root_cause=RootCauseCategory.ACCOUNT_LIFECYCLE,
                root_cause_explanation=(
                    "Merchant formally notified permanent liquidation and retail business closure as of August 31."
                ),
                is_sop_adequate=False,
                override_justification=(
                    "Standard retention outreach is futile and wasteful. Churn is non-preventable due to business liquidation."
                ),
                tailored_action_items=[
                    "Halt automated marketing and promotional retention campaigns to avoid brand nuisance.",
                    "Expedite merchant account closure and release remaining security deposit funds.",
                    "Archive account records per regulatory compliance standards.",
                ],
                recommended_pic="Merchant Operations & Compliance",
                urgency="LOW_MONITOR",
            )
        elif "stable" in customer:
            intervention = ContextAwareIntervention(
                primary_root_cause=RootCauseCategory.GENERAL_SATISFIED,
                root_cause_explanation=(
                    "Merchant is actively operating with routine inquiries regarding promotional shipping subsidies (Campaign 10.10) "
                    "and instant courier activation."
                ),
                is_sop_adequate=True,
                override_justification=(
                    "Account is stable with normal growth inquiries; standard CRM monitoring applies alongside activating requested courier services."
                ),
                tailored_action_items=[
                    "Maintain standard CRM automated monitoring and milestone loyalty perks.",
                    "Coordinate with logistics partner support to activate requested instant and sameday courier integration.",
                ],
                recommended_pic="Automated CRM & Logistics Partner Support",
                urgency="LOW_MONITOR",
            )
        else:
            intervention = ContextAwareIntervention(
                primary_root_cause=RootCauseCategory.GENERAL_SATISFIED,
                root_cause_explanation=(
                    "Account exhibits healthy operations and routine inquiries regarding tax invoice consolidation and staff roles."
                ),
                is_sop_adequate=True,
                override_justification="Account is healthy; standard automated monitoring and milestone appreciation apply.",
                tailored_action_items=[
                    "Dispatch automated quarterly appreciation note and partner loyalty perks.",
                    "Conduct routine check-in for upcoming branch outlet expansions.",
                ],
                recommended_pic="Automated CRM / Customer Success",
                urgency="LOW_MONITOR",
            )

        intervention.ticket_evaluations = tickets_evidence
        token_usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        return intervention, tickets_evidence, token_usage
