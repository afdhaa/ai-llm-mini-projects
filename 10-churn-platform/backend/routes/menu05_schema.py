import time
from typing import Any, Literal
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field
from llm_factory import get_llm, extract_token_usage
from routes.common import get_customer_profile, load_target_customers

menu05_bp = Blueprint("menu05", __name__)


class ActionItem(BaseModel):
    priority: Literal["P1", "P2", "P3"] = Field(description="Priority of retention action.")
    channel: Literal["EMAIL", "PHONE", "IN_APP", "EXECUTIVE_VISIT"] = Field(description="Outreach channel.")
    pic: str = Field(description="Assigned role (e.g. Senior AM, CS Lead).")
    task: str = Field(description="Concrete retention task.")


class ChurnAssessment(BaseModel):
    customer: str = Field(description="Customer name.")
    calibrated_churn_probability: float = Field(description="Exact probability 0.0 to 1.0 from ML.")
    risk_level: Literal["HIGH RISK", "MEDIUM RISK", "LOW RISK", "NO RISK"] = Field(description="Risk category.")
    key_churn_drivers: list[str] = Field(description="Top 2-3 factors driving risk.")
    executive_summary: str = Field(description="Structured 2-sentence summary.")
    prescribed_actions: list[ActionItem] = Field(description="List of concrete action items.")


@menu05_bp.route("/api/tier05/structured", methods=["POST"])
def evaluate_structured():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")
        mode = data.get("mode", "single")

        llm = get_llm(request)
        structured_llm = llm.with_structured_output(ChurnAssessment, method="function_calling", include_raw=True)

        if mode == "batch":
            targets = load_target_customers()
            assessments = []
            total_prompt_tok = 0
            total_comp_tok = 0

            for t in targets:
                prof = get_customer_profile(t["customer"])
                prompt = f"""Evaluate merchant {prof['customer']}:
- ML Churn Probability: {prof['churn_probability']:.1%}
- Risk Tier: {prof['ml_risk_level']}
- Transactions: {prof['transactions']}
- Active Days: {prof['active_days']}
- Inactive Days: {prof['inactive_days']}"""

                resp = structured_llm.invoke(prompt)
                parsed = resp["parsed"]
                toks = extract_token_usage(resp.get("raw"))
                total_prompt_tok += toks.prompt_tokens
                total_comp_tok += toks.completion_tokens
                assessments.append(parsed.model_dump())

            latency_ms = int((time.time() - t0) * 1000)
            return jsonify({
                "success": True,
                "mode": "batch",
                "total_accounts": len(assessments),
                "assessments": assessments,
                "latency_ms": latency_ms,
                "token_usage": {
                    "prompt_tokens": total_prompt_tok,
                    "completion_tokens": total_comp_tok,
                    "total_tokens": total_prompt_tok + total_comp_tok,
                },
            })

        else:
            profile = get_customer_profile(customer)
            prompt = f"""Evaluate merchant {profile['customer']} and return a validated ChurnAssessment contract:
- ML Churn Probability: {profile['churn_probability']:.1%}
- Risk Tier: {profile['ml_risk_level']}
- Transactions: {profile['transactions']}
- Active Days: {profile['active_days']}
- Inactive Days: {profile['inactive_days']}"""

            resp = structured_llm.invoke(prompt)
            assessment: ChurnAssessment = resp["parsed"]
            tokens = extract_token_usage(resp.get("raw"))
            latency_ms = int((time.time() - t0) * 1000)

            return jsonify({
                "success": True,
                "mode": "single",
                "customer": profile["customer"],
                "assessment": assessment.model_dump(),
                "schema_definition": ChurnAssessment.model_json_schema(),
                "latency_ms": latency_ms,
                "token_usage": tokens.model_dump(),
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
