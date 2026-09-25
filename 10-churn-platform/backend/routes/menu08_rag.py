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
