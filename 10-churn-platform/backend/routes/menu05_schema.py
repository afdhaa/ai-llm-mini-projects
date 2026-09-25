import json
import re
import time
from typing import Any
from flask import Blueprint, jsonify, request
from pydantic import BaseModel, Field
from llm_factory import get_llm, extract_token_usage
from routes.common import get_customer_profile, load_target_customers, normalize_llm_content

menu05_bp = Blueprint("menu05", __name__)


class ActionItem(BaseModel):
    priority: str = Field(default="P2", description="Priority of retention action (P1, P2, or P3).")
    channel: str = Field(default="EMAIL", description="Outreach channel (EMAIL, PHONE, IN_APP, EXECUTIVE_VISIT).")
    pic: str = Field(default="Account Manager", description="Assigned role (e.g. Senior AM, CS Lead).")
    task: str = Field(default="Proactive merchant check-in", description="Concrete retention task.")


class ChurnAssessment(BaseModel):
    customer: str = Field(description="Customer name.")
    calibrated_churn_probability: float = Field(description="Exact probability 0.0 to 1.0 from ML.")
    risk_level: str = Field(description="Risk category (HIGH RISK, MEDIUM RISK, LOW RISK, NO RISK).")
    key_churn_drivers: list[str] = Field(default_factory=list, description="Top 2-3 factors driving risk.")
    executive_summary: str = Field(default="", description="Structured 2-sentence summary.")
    prescribed_actions: list[ActionItem] = Field(default_factory=list, description="List of concrete action items.")


def _build_fallback_assessment(prof: dict[str, Any]) -> dict[str, Any]:
    """Deterministic fallback conforming 100% to ChurnAssessment schema."""
    risk = prof.get("ml_risk_level", "MEDIUM RISK")
    prob = float(prof.get("churn_probability", 0.5))
    name = prof.get("customer", "Customer")

    if "HIGH" in risk:
        summary = (
            f"Critical risk account: {name} shows severe disengagement ({prof.get('inactive_days', 0)} inactive days) "
            f"with {prob:.1%} calibrated churn probability. Immediate executive intervention is required."
        )
        actions = [
            ActionItem(priority="P1", channel="EXECUTIVE_VISIT", pic="Strategic VP & Senior AM", task="Schedule urgent executive retention sync to diagnose friction points."),
            ActionItem(priority="P2", channel="PHONE", pic="Solutions Engineer", task="Conduct technical audit on transaction drop-off and API webhooks."),
        ]
    elif "MEDIUM" in risk:
        summary = (
            f"Watchlist account: {name} exhibits declining activity ({prof.get('inactive_days', 0)} inactive days) "
            f"with {prob:.1%} calibrated churn probability. Proactive outreach recommended to avoid churn."
        )
        actions = [
            ActionItem(priority="P2", channel="PHONE", pic="Customer Success Lead", task="Contact merchant lead to review platform usage and address feature concerns."),
            ActionItem(priority="P3", channel="EMAIL", pic="Growth Specialist", task="Share optimization guidelines and feature adoption incentives."),
        ]
    else:
        summary = (
            f"Healthy account: {name} remains engaged with {prob:.1%} calibrated churn probability "
            f"across {prof.get('transactions', 0)} monthly transactions."
        )
        actions = [
            ActionItem(priority="P3", channel="IN_APP", pic="Account Manager", task="Deliver standard quarterly appreciation update and roadmap sneak-peek."),
        ]

    return ChurnAssessment(
        customer=name,
        calibrated_churn_probability=prob,
        risk_level=risk,
        key_churn_drivers=[
            f"Monthly order volume: {prof.get('transactions', 0)} transactions",
            f"Active days: {prof.get('active_days', 0)} of past 30 days",
            f"Dormant gap: {prof.get('inactive_days', 0)} consecutive days inactive",
        ],
        executive_summary=summary,
        prescribed_actions=actions,
    ).model_dump()


def _coerce_churn_assessment_dict(data: dict[str, Any], prof: dict[str, Any]) -> dict[str, Any]:
    """Coerce partial or loosely-typed dictionary into validated ChurnAssessment."""
    try:
        prob = data.get("calibrated_churn_probability")
        if prob is None or not isinstance(prob, (int, float)):
            prob = float(prof.get("churn_probability", 0.5))
        else:
            prob = float(prob)
            if prob > 1.0:
                prob = prob / 100.0

        actions = []
        for a in data.get("prescribed_actions", []):
            if isinstance(a, dict):
                actions.append(ActionItem(
                    priority=str(a.get("priority", "P2")),
                    channel=str(a.get("channel", "EMAIL")),
                    pic=str(a.get("pic", "Account Lead")),
                    task=str(a.get("task", "Operational outreach")),
                ))

        drivers = data.get("key_churn_drivers")
        if not isinstance(drivers, list):
            drivers = [str(drivers)] if drivers else []

        assessment = ChurnAssessment(
            customer=str(data.get("customer", prof["customer"])),
            calibrated_churn_probability=prob,
            risk_level=str(data.get("risk_level", prof.get("ml_risk_level", "MEDIUM RISK"))),
            key_churn_drivers=drivers or [f"Platform inactivity: {prof.get('inactive_days', 0)} days"],
            executive_summary=str(data.get("executive_summary") or f"Evaluation for {prof['customer']}."),
            prescribed_actions=actions or [
                ActionItem(priority="P1", channel="EMAIL", pic="Account Manager", task="Proactive outreach regarding account engagement.")
            ],
        )
        return assessment.model_dump()
    except Exception:
        return _build_fallback_assessment(prof)


def safe_extract_churn_assessment(resp: Any, prof: dict[str, Any]) -> dict[str, Any]:
    """Robustly extract and validate ChurnAssessment payload, handling NoneType or malformed tool calls."""
    if isinstance(resp, dict):
        parsed = resp.get("parsed")
        if parsed is not None:
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()
            if isinstance(parsed, dict):
                return _coerce_churn_assessment_dict(parsed, prof)

        raw = resp.get("raw")
        if raw is not None:
            # 1. Tool calls
            if hasattr(raw, "tool_calls") and raw.tool_calls:
                for tc in raw.tool_calls:
                    args = tc.get("args")
                    if args and isinstance(args, dict):
                        return _coerce_churn_assessment_dict(args, prof)

            # 2. Function calls in additional_kwargs
            if hasattr(raw, "additional_kwargs") and raw.additional_kwargs:
                fc = raw.additional_kwargs.get("function_call") or {}
                if fc.get("arguments"):
                    try:
                        args = json.loads(fc["arguments"])
                        return _coerce_churn_assessment_dict(args, prof)
                    except Exception:
                        pass

            # 3. Content parsing for JSON
            content = getattr(raw, "content", "")
            if content:
                content_str = normalize_llm_content(content)
                json_match = re.search(r"(\{.*\})", content_str, re.DOTALL)
                if json_match:
                    try:
                        args = json.loads(json_match.group(1))
                        return _coerce_churn_assessment_dict(args, prof)
                    except Exception:
                        pass
    elif hasattr(resp, "model_dump"):
        return resp.model_dump()

    return _build_fallback_assessment(prof)


@menu05_bp.route("/api/tier05/structured", methods=["POST"])
def evaluate_structured():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")
        mode = data.get("mode", "single")

        llm = get_llm(request)
        try:
            structured_llm = llm.with_structured_output(ChurnAssessment, include_raw=True)
        except Exception:
            structured_llm = llm.with_structured_output(ChurnAssessment, method="function_calling", include_raw=True)

        if mode == "batch":
            targets = load_target_customers()
            assessments = []
            total_prompt_tok = 0
            total_comp_tok = 0

            for t in targets:
                prof = get_customer_profile(t["customer"])
                prompt = f"""Evaluate merchant {prof['customer']} and return a validated ChurnAssessment schema:
- Customer: {prof['customer']}
- ML Churn Probability: {prof['churn_probability']:.1%}
- Risk Tier: {prof['ml_risk_level']}
- Transactions: {prof['transactions']}
- Active Days: {prof['active_days']}
- Inactive Days: {prof['inactive_days']}"""

                try:
                    resp = structured_llm.invoke(prompt)
                    toks = extract_token_usage(resp.get("raw") if isinstance(resp, dict) else resp)
                    total_prompt_tok += toks.prompt_tokens
                    total_comp_tok += toks.completion_tokens
                    assessment_data = safe_extract_churn_assessment(resp, prof)
                except Exception:
                    assessment_data = _build_fallback_assessment(prof)

                assessments.append(assessment_data)

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
- Customer: {profile['customer']}
- ML Churn Probability: {profile['churn_probability']:.1%}
- Risk Tier: {profile['ml_risk_level']}
- Transactions: {profile['transactions']}
- Active Days: {profile['active_days']}
- Inactive Days: {profile['inactive_days']}"""

            try:
                resp = structured_llm.invoke(prompt)
                tokens = extract_token_usage(resp.get("raw") if isinstance(resp, dict) else resp)
                assessment_data = safe_extract_churn_assessment(resp, profile)
            except Exception:
                tokens = extract_token_usage(None)
                assessment_data = _build_fallback_assessment(profile)

            latency_ms = int((time.time() - t0) * 1000)

            return jsonify({
                "success": True,
                "mode": "single",
                "customer": profile["customer"],
                "assessment": assessment_data,
                "schema_definition": ChurnAssessment.model_json_schema(),
                "latency_ms": latency_ms,
                "token_usage": tokens.model_dump(),
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
