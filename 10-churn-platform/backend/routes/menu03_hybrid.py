import time
from flask import Blueprint, jsonify, request
from llm_factory import get_llm, extract_token_usage
from routes.common import get_customer_profile

menu03_bp = Blueprint("menu03", __name__)

HYBRID_PROMPT_TEMPLATE = """You are a Senior Strategic Account Manager at a leading B2B e-commerce platform.
Write a formal, actionable account retention briefing for account: "{customer}".

QUANTITATIVE MACHINE LEARNING SIGNALS (Statistical Truth):
- Calibrated Churn Probability : {churn_percentage}
- Statistical Risk Tier        : [{ml_risk_level}]
- Monthly Transactions         : {transactions}
- Active Days (Last 30 Days)   : {active_days}
- Inactive Days                : {inactive_days}

INSTRUCTIONS:
1. Ground your reasoning strictly on the statistical churn risk ({churn_percentage}). Do not invent different probability numbers.
2. Provide a 2-paragraph Account Risk Summary explaining the behavioral drivers behind this score.
3. Prescribe 3 concrete intervention steps tailored to this risk level.
"""


@menu03_bp.route("/api/tier03/briefing", methods=["POST"])
def generate_hybrid_briefing():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")
        profile = get_customer_profile(customer)

        prompt = HYBRID_PROMPT_TEMPLATE.format(
            customer=profile["customer"],
            churn_percentage=f"{profile['churn_probability']:.1%}",
            ml_risk_level=profile["ml_risk_level"],
            transactions=profile["transactions"],
            active_days=profile["active_days"],
            inactive_days=profile["inactive_days"],
        )

        llm = get_llm(request)
        resp = llm.invoke(prompt)
        latency_ms = int((time.time() - t0) * 1000)
        tokens = extract_token_usage(resp)

        return jsonify({
            "success": True,
            "customer": profile["customer"],
            "churn_probability": profile["churn_probability"],
            "churn_percentage": f"{profile['churn_probability']:.1%}",
            "ml_risk_level": profile["ml_risk_level"],
            "transactions": profile["transactions"],
            "active_days": profile["active_days"],
            "inactive_days": profile["inactive_days"],
            "prompt": prompt,
            "briefing": str(resp.content),
            "latency_ms": latency_ms,
            "token_usage": tokens.model_dump(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
