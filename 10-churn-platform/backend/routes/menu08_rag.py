import json
import time
from typing import Any, Literal
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field
from llm_factory import get_llm, extract_token_usage
from routes.common import get_customer_profile, load_retention_playbook

menu08_bp = Blueprint("menu08", __name__)


class ContextAwareIntervention(BaseModel):
    primary_root_cause: Literal[
        "TECHNICAL_BUG",
        "PRICING_COMMERCIAL",
        "SERVICE_QUALITY",
        "ACCOUNT_LIFECYCLE",
        "GENERAL_SATISFIED",
    ] = Field(description="Primary root cause diagnosed from tickets.")
    is_sop_adequate: bool = Field(description="False if generic SOP (e.g. 25% discount) is counterproductive.")
    override_justification: str = Field(description="Why generic discounts are rejected or adjusted.")
    urgency: Literal["CRITICAL", "HIGH", "MEDIUM", "ROUTINE"] = Field(description="Operational urgency.")
    recommended_pic: str = Field(description="Appropriate team role to own this account.")
    tailored_action_items: list[str] = Field(description="3-4 concrete actions addressing genuine root cause.")


RAG_SYNTHESIS_PROMPT = """You are an Enterprise Retention Director synthesizing quantitative ML scores with qualitative customer support signals.

CUSTOMER: {customer}
- ML Churn Probability : {churn_percentage} [{risk_level}]
- Activity Signals      : {transactions} transactions, {active_days} active days, {inactive_days} inactive days

GENERIC PLAYBOOK SOP (Tabular Guidance):
- Prescribed Generic Incentive: {generic_incentive}
- Default Generic Actions: {generic_actions}

UNSTRUCTURED SUPPORT TICKETS & WHATSAPP LOGS (RAG Context):
{tickets_json}

INSTRUCTIONS:
1. Examine the retrieved support tickets to discover the true underlying problem.
2. Determine whether the generic SOP (e.g. offering a discount voucher) is adequate or tone-deaf (e.g. if the customer's webhooks or payouts are broken, a discount damages trust).
3. Return a validated ContextAwareIntervention schema.
"""


@menu08_bp.route("/api/tier08/rag", methods=["POST"])
def evaluate_rag():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")
        profile = get_customer_profile(customer)

        playbooks = load_retention_playbook()
        pb_match = next((p for p in playbooks if p.get("risk_level", "").upper() == profile["ml_risk_level"].replace(" RISK", "")), playbooks[0])

        prompt = RAG_SYNTHESIS_PROMPT.format(
            customer=profile["customer"],
            churn_percentage=f"{profile['churn_probability']:.1%}",
            risk_level=profile["ml_risk_level"],
            transactions=profile["transactions"],
            active_days=profile["active_days"],
            inactive_days=profile["inactive_days"],
            generic_incentive=pb_match.get("incentive", "None"),
            generic_actions=pb_match.get("actions", ""),
            tickets_json=json.dumps(profile["tickets"], indent=2, ensure_ascii=False),
        )

        llm = get_llm(request)
        structured_llm = llm.with_structured_output(ContextAwareIntervention, method="function_calling", include_raw=True)

        resp = structured_llm.invoke(prompt)
        intervention: ContextAwareIntervention = resp["parsed"]
        tokens = extract_token_usage(resp.get("raw"))
        latency_ms = int((time.time() - t0) * 1000)

        return jsonify({
            "success": True,
            "customer": profile["customer"],
            "churn_probability": profile["churn_probability"],
            "ml_risk_level": profile["ml_risk_level"],
            "generic_sop": {
                "incentive": pb_match.get("incentive"),
                "actions": [a.strip() for a in str(pb_match.get("actions", "")).split(";") if a.strip()],
            },
            "retrieved_tickets": profile["tickets"],
            "tailored_intervention": intervention.model_dump(),
            "latency_ms": latency_ms,
            "token_usage": tokens.model_dump(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@menu08_bp.route("/api/tier08/matrix", methods=["GET"])
def get_rag_matrix():
    """Return comparative intelligence summary across all target merchants."""
    try:
        from routes.common import load_target_customers
        targets = load_target_customers()
        playbooks = load_retention_playbook()

        matrix = []
        for t in targets:
            prof = get_customer_profile(t["customer"])
            risk = prof["ml_risk_level"].replace(" RISK", "")
            pb_match = next((p for p in playbooks if p.get("risk_level", "").upper() == risk), playbooks[0])

            # Diagnosed baseline from tickets
            tickets = prof["tickets"]
            has_bug = any("504" in tk.get("message", "") or "webhook" in tk.get("message", "").lower() for tk in tickets)
            has_pricing = any("komisi" in tk.get("message", "").lower() or "fee" in tk.get("message", "").lower() for tk in tickets)
            has_closed = any("tutup" in tk.get("message", "").lower() or "likuidasi" in tk.get("message", "").lower() for tk in tickets)

            if has_bug:
                rc = "TECHNICAL_BUG"
                sop_ok = False
                tailored = "Urgent P1 DevOps escalation for webhook fix + unfreeze payout. Vouchers rejected."
            elif has_pricing:
                rc = "PRICING_COMMERCIAL"
                sop_ok = False
                tailored = "Override vouchers; initiate volume-tiered commercial renegotiation."
            elif has_closed:
                rc = "ACCOUNT_LIFECYCLE"
                sop_ok = False
                tailored = "Non-preventable churn. Halt marketing campaigns and expedite account closure."
            else:
                rc = "GENERAL_SATISFIED"
                sop_ok = True
                tailored = "Routine CRM partner loyalty perks; maintain standard account success check-ins."

            matrix.append({
                "customer": prof["customer"],
                "churn_probability": prof["churn_probability"],
                "churn_percentage": f"{prof['churn_probability']:.1%}",
                "ml_risk_level": prof["ml_risk_level"],
                "generic_sop_incentive": pb_match.get("incentive"),
                "ticket_count": len(tickets),
                "tickets_summary": [f"[{tk.get('ticket_id')}] {tk.get('subject')}" for tk in tickets[:2]],
                "primary_root_cause": rc,
                "is_sop_adequate": sop_ok,
                "tailored_action_summary": tailored,
            })

        matrix.sort(key=lambda x: x["churn_probability"], reverse=True)
        return jsonify({"success": True, "total_accounts": len(matrix), "matrix": matrix})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
