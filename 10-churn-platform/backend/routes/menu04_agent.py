import json
import time
from typing import Any
import pandas as pd
from flask import Blueprint, jsonify, request
from langchain_core.tools import tool
from llm_factory import get_llm, extract_token_usage, TokenUsage
from routes.common import DATA_DIR, load_ml_model, load_target_customers, load_retention_playbook

menu04_bp = Blueprint("menu04", __name__)


def create_agent_tools():
    """Build LangChain tools dynamically grounded on backend data assets."""

    @tool
    def get_target_customers_tool() -> str:
        """Fetch list of target customer accounts currently evaluated for churn risk."""
        targets = load_target_customers()
        return json.dumps(targets, indent=2)

    @tool
    def list_historical_customers_tool(limit: int = 5) -> str:
        """Fetch a sample of historical merchant records with churned/active statuses."""
        df = pd.read_csv(DATA_DIR / "customers.csv")
        return df.head(limit).to_dict(orient="records")

    @tool
    def predict_churn_risk_tool(transactions: float, active_days: float, inactive_days: float) -> str:
        """Calculate calibrated churn probability (%) using the trained Scikit-Learn model."""
        model = load_ml_model()
        feats = pd.DataFrame([{
            "transactions": float(transactions),
            "active_days": float(active_days),
            "inactive_days": float(inactive_days),
        }])
        prob = float(model.predict_proba(feats)[0][1])
        tier = "HIGH" if prob >= 0.75 else ("MEDIUM" if prob >= 0.50 else ("LOW" if prob >= 0.20 else "NO RISK"))
        return json.dumps({"churn_probability": prob, "churn_percentage": f"{prob:.1%}", "risk_tier": tier})

    @tool
    def get_retention_playbook_tool(risk_tier: str) -> str:
        """Fetch company standard operating procedure (SOP) retention actions for a risk tier."""
        pbs = load_retention_playbook()
        match = next((p for p in pbs if p.get("risk_level", "").upper() == risk_tier.upper()), None)
        if match:
            return json.dumps(match)
        return json.dumps(pbs)

    return [
        get_target_customers_tool,
        list_historical_customers_tool,
        predict_churn_risk_tool,
        get_retention_playbook_tool,
    ]


@menu04_bp.route("/api/tier04/chat", methods=["POST"])
def agent_chat():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        user_query = data.get(
            "query",
            "Evaluate Store Critical: predict churn probability using the ML model and suggest retention SOP.",
        )

        tools = create_agent_tools()
        tools_map = {t.name: t for t in tools}
        llm = get_llm(request)
        llm_with_tools = llm.bind_tools(tools)

        tool_timeline: list[dict[str, Any]] = []
        messages = [
            ("system", "You are an autonomous customer retention assistant with access to customer databases, "
                       "Scikit-Learn ML models, and retention playbooks. Solve the user request by deciding which tools to call."),
            ("user", user_query),
        ]

        total_tokens = TokenUsage()
        max_turns = 6

        for turn in range(max_turns):
            resp = llm_with_tools.invoke(messages)
            tokens = extract_token_usage(resp)
            total_tokens = total_tokens.add(tokens)
            messages.append(resp)

            if not resp.tool_calls:
                break

            for tc in resp.tool_calls:
                t_name = tc["name"]
                t_args = tc["args"]
                t_tool = tools_map.get(t_name)
                if t_tool:
                    try:
                        observation = t_tool.invoke(t_args)
                    except Exception as err:
                        observation = f"Tool execution error: {str(err)}"
                else:
                    observation = f"Tool '{t_name}' not found."

                tool_timeline.append({
                    "turn": turn + 1,
                    "tool": t_name,
                    "arguments": t_args,
                    "observation": str(observation),
                })
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(tool_call_id=tc["id"], content=str(observation)))

        latency_ms = int((time.time() - t0) * 1000)

        final_answer = str(messages[-1].content) if hasattr(messages[-1], "content") else str(messages[-1])

        return jsonify({
            "success": True,
            "query": user_query,
            "final_answer": final_answer,
            "tool_timeline": tool_timeline,
            "total_tools_called": len(tool_timeline),
            "latency_ms": latency_ms,
            "token_usage": total_tokens.model_dump(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
