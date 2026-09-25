import time
from flask import Blueprint, jsonify, request
from llm_factory import get_llm, extract_token_usage
from routes.common import get_customer_profile, normalize_llm_content

menu02_bp = Blueprint("menu02", __name__)

PROMPT_TEMPLATE = """You are an expert customer retention analyst in an e-commerce platform.
Evaluate the following merchant's account activity and qualitative churn risk:

CUSTOMER: {customer}
- Monthly Transactions: {transactions}
- Active Days (Past 30d): {active_days}
- Inactive Days: {inactive_days}

Provide a concise, professional assessment containing:
1. Qualitative Risk Tier (High / Medium / Low / None)
2. Behavioral Diagnosis (Why are they behaving this way?)
3. Immediate Retention Recommendation
"""


@menu02_bp.route("/api/tier02/evaluate", methods=["POST"])
def evaluate_pure_llm():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")

        try:
            profile = get_customer_profile(customer)
            tx = profile["transactions"]
            act = profile["active_days"]
            inact = profile["inactive_days"]
        except Exception:
            tx = int(data.get("transactions", 45))
            act = int(data.get("active_days", 5))
            inact = int(data.get("inactive_days", 30))

        custom_prompt = data.get("custom_prompt")
        if custom_prompt and custom_prompt.strip():
            try:
                prompt = custom_prompt.format(
                    customer=customer,
                    transactions=tx,
                    active_days=act,
                    inactive_days=inact,
                )
            except Exception:
                prompt = custom_prompt
        else:
            prompt = PROMPT_TEMPLATE.format(
                customer=customer,
                transactions=tx,
                active_days=act,
                inactive_days=inact,
            )

        llm = get_llm(request)
        resp = llm.invoke(prompt)
        latency_ms = int((time.time() - t0) * 1000)
        tokens = extract_token_usage(resp)

        return jsonify({
            "success": True,
            "customer": customer,
            "prompt": prompt,
            "response": normalize_llm_content(resp.content),
            "latency_ms": latency_ms,
            "token_usage": tokens.model_dump(),
            "characteristics": "Zero ML training required; rich qualitative reasoning; subjective numerical estimation.",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
