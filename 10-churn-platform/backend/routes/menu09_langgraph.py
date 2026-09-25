import json
import time
from pathlib import Path
from typing import Any, Literal, TypedDict
from flask import Blueprint, Response, jsonify, request
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from llm_factory import extract_token_usage, get_llm, get_llm_config_from_request, TokenUsage
from routes.common import DATA_DIR, get_customer_profile, load_retention_playbook

menu09_bp = Blueprint("menu09", __name__)
AUDIT_FILE = DATA_DIR / "execution_audit.json"


# --- Schemas ---

class DiagnosticFindings(BaseModel):
    root_cause: Literal[
        "TECHNICAL_BUG",
        "BILLING_SETTLEMENT",
        "PRICING_COMMERCIAL",
        "SERVICE_QUALITY",
        "ACCOUNT_LIFECYCLE",
        "GENERAL_SATISFIED",
    ] = Field(description="Primary root cause category.")
    technical_severity: Literal["CRITICAL_P1", "HIGH_P2", "MEDIUM_P3", "LOW_P4", "NONE"] = Field(
        description="Severity of technical blocker."
    )
    key_blocker: str = Field(description="One-sentence description of the core bottleneck.")
    diagnostic_summary: str = Field(description="Detailed technical/operational analysis.")
    requires_technical_escalation: bool = Field(description="Whether engineering/DevOps is required.")


class FinancialAssessment(BaseModel):
    customer_tier: str = Field(description="Customer tier (e.g. ENTERPRISE, GROWTH).")
    monthly_gmv_idr: float = Field(description="Monthly GMV in IDR.")
    monthly_revenue_idr: float = Field(description="Platform revenue in IDR.")
    pending_payout_idr: float = Field(description="Funds currently held or pending settlement.")
    max_retention_budget_idr: float = Field(description="Maximum authorized retention budget cap.")
    financial_risk_verdict: Literal["HIGH_EXPOSURE", "MODERATE_EXPOSURE", "LOW_EXPOSURE"] = Field(
        description="Financial exposure level."
    )
    approved_budget_cap_idr: float = Field(description="Strict monetary ceiling for incentives.")
    commercial_rationale: str = Field(description="Strategic justification based on merchant LTV.")


class RetentionActionItem(BaseModel):
    action_type: Literal[
        "CRM_OUTREACH",
        "DEVOPS_INCIDENT",
        "FINANCE_PAYOUT_RELEASE",
        "FEE_WAIVER_OR_DISCOUNT",
        "COMMERCIAL_RENEGOTIATION",
        "ACCOUNT_OFFBOARDING",
    ] = Field(description="Type of operational side-effect.")
    title: str = Field(description="Action title.")
    description: str = Field(description="Detailed action instructions.")
    owner_role: str = Field(description="Role responsible.")
    cost_idr: float = Field(default=0.0, description="Financial expenditure or waiver in IDR.")
    requires_human_approval: bool = Field(default=False, description="Whether human approval is required.")


class RetentionProposal(BaseModel):
    summary: str = Field(description="Executive summary of retention plan.")
    primary_root_cause: str = Field(description="Harmonized root cause agreed upon.")
    total_proposed_cost_idr: float = Field(description="Total monetary cost of proposed incentives/waivers.")
    is_override_sop: bool = Field(description="Whether standard SOP was overridden.")
    override_reason: str = Field(description="Why SOP was modified.")
    action_items: list[RetentionActionItem] = Field(description="List of concrete actions.")
    requires_hitl: bool = Field(description="Whether human review is required.")
    hitl_reason: str = Field(description="Condition that triggered human review.")


class ExecutionLogItem(BaseModel):
    action_type: str
    target_system: str
    payload: dict[str, Any]
    status: Literal["DISPATCHED", "SIMULATED", "SKIPPED", "BLOCKED"]
    message: str


class AgentState(TypedDict):
    customer_id: str
    transactions: int
    active_days: int
    inactive_days: int
    churn_probability: float
    ml_risk_level: str
    support_tickets: list[dict[str, Any]]
    financials: dict[str, Any]
    sop_baseline: dict[str, Any]
    diagnostic_findings: dict[str, Any] | None
    financial_assessment: dict[str, Any] | None
    proposal: dict[str, Any] | None
    hitl_status: Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "AUTO_APPROVED"]
    human_feedback: str | None
    approved_action_indices: list[int] | None
    execution_logs: list[dict[str, Any]]
    token_usage: dict[str, int]


def execute_action(action: RetentionActionItem, customer: str) -> ExecutionLogItem:
    a_type = action.action_type
    if a_type == "DEVOPS_INCIDENT":
        target = "PagerDuty & Jira Service Desk"
        payload = {
            "project": "DEV",
            "priority": "P1",
            "summary": f"[CRITICAL CHURN BLOCKER] {customer}: {action.title}",
            "assignee_role": action.owner_role,
            "description": action.description,
            "sla_hours": 4,
        }
        msg = f"Dispatched P1 Incident to {target}. SLA: 4 hours."
    elif a_type == "FINANCE_PAYOUT_RELEASE":
        target = "Fintech Settlement Engine & Core Banking"
        payload = {
            "account": customer,
            "amount_idr": action.cost_idr,
            "authorization": "CHURN_PREVENTION_EMERGENCY_RELEASE",
            "reference": f"PAYOUT-REL-{customer.replace(' ', '-').upper()}",
            "note": action.description,
        }
        msg = f"Unfroze settlement payout of Rp {action.cost_idr:,.0f} via {target}."
    elif a_type == "FEE_WAIVER_OR_DISCOUNT":
        target = "Billing & Subscription Gateway"
        payload = {
            "customer": customer,
            "credit_value_idr": action.cost_idr,
            "type": "PLATFORM_FEE_WAIVER",
            "notes": action.description,
        }
        msg = f"Applied platform fee credit / waiver valued at Rp {action.cost_idr:,.0f}."
    elif a_type == "COMMERCIAL_RENEGOTIATION":
        target = "Salesforce Enterprise CRM"
        payload = {
            "account": customer,
            "stage": "CONTRACT_RENEGOTIATION",
            "lead": action.owner_role,
            "notes": action.description,
        }
        msg = f"Logged high-priority commercial contract renegotiation in {target}."
    elif a_type == "ACCOUNT_OFFBOARDING":
        target = "Customer Marketing Hub & Account Registry"
        payload = {
            "account": customer,
            "marketing_status": "SUPPRESSED",
            "status": "GRACEFUL_OFFBOARDING",
            "reason": action.description,
        }
        msg = f"Halted active campaigns and initiated offboarding workflow in {target}."
    else:
        target = "Zendesk & CRM Outreach Module"
        payload = {
            "customer": customer,
            "task": action.title,
            "assigned_to": action.owner_role,
            "instructions": action.description,
        }
        msg = f"Created high-touch outreach task in {target}."

    return ExecutionLogItem(action_type=a_type, target_system=target, payload=payload, status="DISPATCHED", message=msg)


# --- Persistent Session Checkpointer Storage ---
GLOBAL_MEMORY = MemorySaver()
ACTIVE_GRAPHS: dict[str, Any] = {}
REQUEST_LLM_CONFIGS: dict[str, dict[str, Any]] = {}


def get_or_build_graph(thread_id: str, req_config: dict[str, Any] | None = None):
    REQUEST_LLM_CONFIGS[thread_id] = req_config or {}

    def diagnose_node(state: AgentState) -> dict[str, Any]:
        cfg = REQUEST_LLM_CONFIGS.get(thread_id, {})
        llm = get_llm(override_config=cfg)
        structured = llm.with_structured_output(DiagnosticFindings, method="function_calling", include_raw=True)
        prompt = f"""You are the Lead Technical & Diagnostics Specialist in an enterprise retention squad.
TARGET MERCHANT: {state['customer_id']}
ML CHURN PROBABILITY: {state['churn_probability']:.1%} [{state['ml_risk_level']}]
ACTIVITY: {state['transactions']} transactions, {state['active_days']} active days, {state['inactive_days']} inactive days.
SUPPORT TICKETS:
{json.dumps(state['support_tickets'], indent=2, ensure_ascii=False)}
"""
        resp = structured.invoke(prompt)
        findings: DiagnosticFindings = resp["parsed"]
        toks = extract_token_usage(resp.get("raw"))
        current_toks = TokenUsage.model_validate(state.get("token_usage") or {})
        return {
            "diagnostic_findings": findings.model_dump(),
            "token_usage": current_toks.add(toks).model_dump(),
        }

    def finance_node(state: AgentState) -> dict[str, Any]:
        cfg = REQUEST_LLM_CONFIGS.get(thread_id, {})
        llm = get_llm(override_config=cfg)
        structured = llm.with_structured_output(FinancialAssessment, method="function_calling", include_raw=True)
        diag = state.get("diagnostic_findings") or {}
        prompt = f"""You are the Head of Commercial Strategy & Finance in an enterprise retention squad.
TARGET MERCHANT: {state['customer_id']}
FINANCIAL PROFILE:
{json.dumps(state['financials'], indent=2, ensure_ascii=False)}
ML RISK: {state['churn_probability']:.1%} [{state['ml_risk_level']}]
DIAGNOSTIC FINDINGS:
{json.dumps(diag, indent=2, ensure_ascii=False)}
"""
        resp = structured.invoke(prompt)
        assessment: FinancialAssessment = resp["parsed"]
        toks = extract_token_usage(resp.get("raw"))
        current_toks = TokenUsage.model_validate(state.get("token_usage") or {})
        return {
            "financial_assessment": assessment.model_dump(),
            "token_usage": current_toks.add(toks).model_dump(),
        }

    def synthesizer_node(state: AgentState) -> dict[str, Any]:
        cfg = REQUEST_LLM_CONFIGS.get(thread_id, {})
        llm = get_llm(override_config=cfg)
        structured = llm.with_structured_output(RetentionProposal, method="function_calling", include_raw=True)
        diag = state.get("diagnostic_findings") or {}
        fin = state.get("financial_assessment") or {}
        feedback = state.get("human_feedback") or ""
        feedback_prompt = f"\nHUMAN STEERING DIRECTIVE: {feedback}\n" if feedback else ""

        prompt = f"""You are the Senior Retention Director & Supervisor synthesizing a concrete retention proposal.
TARGET MERCHANT: {state['customer_id']}
ML CHURN PREDICTION: {state['churn_probability']:.1%} [{state['ml_risk_level']}]
STANDARD PLAYBOOK BASELINE:
{json.dumps(state['sop_baseline'], indent=2, ensure_ascii=False)}
DIAGNOSTIC REPORT:
{json.dumps(diag, indent=2, ensure_ascii=False)}
FINANCIAL REPORT:
{json.dumps(fin, indent=2, ensure_ascii=False)}
{feedback_prompt}
Determine if HITL review is required (True if cost > Rp 5M, or churn > 80%, or plan has P1 DevOps/Banking payout release)."""
        resp = structured.invoke(prompt)
        proposal: RetentionProposal = resp["parsed"]
        toks = extract_token_usage(resp.get("raw"))
        current_toks = TokenUsage.model_validate(state.get("token_usage") or {})
        return {
            "proposal": proposal.model_dump(),
            "token_usage": current_toks.add(toks).model_dump(),
        }

    def hitl_gate_node(state: AgentState) -> dict[str, Any]:
        raw_prop = state.get("proposal") or {}
        requires_hitl = raw_prop.get("requires_hitl", True)
        return {"hitl_status": "PENDING_REVIEW" if requires_hitl else "AUTO_APPROVED"}

    def execution_node(state: AgentState) -> dict[str, Any]:
        customer = state["customer_id"]
        status = state.get("hitl_status", "AUTO_APPROVED")
        logs = list(state.get("execution_logs") or [])
        raw_prop = state.get("proposal")
        if not raw_prop:
            return {"execution_logs": logs}

        proposal = RetentionProposal.model_validate(raw_prop)
        approved_indices = state.get("approved_action_indices")

        if status in ("APPROVED", "AUTO_APPROVED"):
            for idx, item in enumerate(proposal.action_items):
                if approved_indices is not None and idx not in approved_indices:
                    logs.append(ExecutionLogItem(
                        action_type=item.action_type,
                        target_system="Safety Interceptor",
                        payload={"action_title": item.title, "cost_idr": item.cost_idr},
                        status="SKIPPED",
                        message=f"Action '{item.title}' omitted by operator.",
                    ).model_dump())
                else:
                    log_item = execute_action(item, customer)
                    logs.append(log_item.model_dump())
        elif status == "REJECTED":
            feedback = state.get("human_feedback") or "Human operator declined proposal execution."
            logs.append(ExecutionLogItem(
                action_type="CANCELLED_BY_HUMAN",
                target_system="Safety Interceptor",
                payload={"proposal_summary": proposal.summary, "reason": feedback},
                status="BLOCKED",
                message=f"Retention proposal rejected by operator: {feedback}",
            ).model_dump())

        # Persist to execution_audit.json
        try:
            with open(AUDIT_FILE, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return {"execution_logs": logs}

    builder = StateGraph(AgentState)
    builder.add_node("diagnose", diagnose_node)
    builder.add_node("finance", finance_node)
    builder.add_node("synthesizer", synthesizer_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("execution", execution_node)

    builder.add_edge(START, "diagnose")
    builder.add_edge("diagnose", "finance")
    builder.add_edge("finance", "synthesizer")
    builder.add_edge("synthesizer", "hitl_gate")
    builder.add_edge("hitl_gate", "execution")
    builder.add_edge("execution", END)

    return builder.compile(checkpointer=GLOBAL_MEMORY, interrupt_after=["hitl_gate"])


def build_initial_state(customer_name: str) -> dict[str, Any]:
    prof = get_customer_profile(customer_name)
    playbooks = load_retention_playbook()
    pb_match = next((p for p in playbooks if p.get("risk_level", "").upper() == prof["ml_risk_level"].replace(" RISK", "")), playbooks[0])
    sop_baseline = {
        "risk_level": prof["ml_risk_level"],
        "sla": pb_match.get("sla", "48h"),
        "pic": pb_match.get("pic", "Account Manager"),
        "generic_incentive": pb_match.get("incentive", "None"),
        "generic_actions": [a.strip() for a in str(pb_match.get("actions", "")).split(";") if a.strip()],
    }
    return {
        "customer_id": prof["customer"],
        "transactions": prof["transactions"],
        "active_days": prof["active_days"],
        "inactive_days": prof["inactive_days"],
        "churn_probability": prof["churn_probability"],
        "ml_risk_level": prof["ml_risk_level"],
        "support_tickets": prof["tickets"],
        "financials": prof["financials"],
        "sop_baseline": sop_baseline,
        "diagnostic_findings": None,
        "financial_assessment": None,
        "proposal": None,
        "hitl_status": "PENDING_REVIEW",
        "human_feedback": None,
        "approved_action_indices": None,
        "execution_logs": [],
        "token_usage": TokenUsage().model_dump(),
    }


@menu09_bp.route("/api/tier09/evaluate", methods=["POST"])
def evaluate_langgraph():
    """Run graph up to hitl_gate pause and return state for human review."""
    try:
        data = request.get_json() or {}
        customer = data.get("customer", "Store Critical")
        session_id = data.get("session_id") or f"session-{customer.replace(' ', '-').lower()}"
        req_cfg = get_llm_config_from_request(request)

        graph = get_or_build_graph(session_id, req_cfg)
        init_state = build_initial_state(customer)
        config = {"configurable": {"thread_id": session_id}}

        state = graph.invoke(init_state, config=config)
        return jsonify({
            "success": True,
            "session_id": session_id,
            "customer": customer,
            "state": state,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@menu09_bp.route("/api/tier09/stream", methods=["GET"])
def stream_langgraph():
    """Server-Sent Events endpoint streaming progress per agent node."""
    customer = request.args.get("customer", "Store Critical")
    session_id = request.args.get("session_id") or f"session-{customer.replace(' ', '-').lower()}"
    req_cfg = get_llm_config_from_request(request)

    def generate_events():
        try:
            yield f"data: {json.dumps({'type': 'init', 'session_id': session_id, 'customer': customer})}\n\n"
            graph = get_or_build_graph(session_id, req_cfg)
            init_state = build_initial_state(customer)
            config = {"configurable": {"thread_id": session_id}}

            yield f"data: {json.dumps({'type': 'node_start', 'node': 'diagnose', 'title': 'Technical Specialist Diagnosing...'})}\n\n"

            for event in graph.stream(init_state, config=config):
                for node_name, node_output in event.items():
                    if node_name == "diagnose":
                        yield f"data: {json.dumps({'type': 'node_done', 'node': 'diagnose', 'data': node_output.get('diagnostic_findings')})}\n\n"
                        yield f"data: {json.dumps({'type': 'node_start', 'node': 'finance', 'title': 'Commercial Specialist Calculating...'})}\n\n"
                    elif node_name == "finance":
                        yield f"data: {json.dumps({'type': 'node_done', 'node': 'finance', 'data': node_output.get('financial_assessment')})}\n\n"
                        yield f"data: {json.dumps({'type': 'node_start', 'node': 'synthesizer', 'title': 'Retention Supervisor Synthesizing...'})}\n\n"
                    elif node_name == "synthesizer":
                        yield f"data: {json.dumps({'type': 'node_done', 'node': 'synthesizer', 'data': node_output.get('proposal')})}\n\n"
                    elif node_name == "hitl_gate":
                        yield f"data: {json.dumps({'type': 'hitl_gate', 'status': node_output.get('hitl_status')})}\n\n"

            current_state = graph.get_state(config).values
            yield f"data: {json.dumps({'type': 'ready_for_review', 'session_id': session_id, 'state': current_state})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate_events(), mimetype="text/event-stream")


@menu09_bp.route("/api/tier09/action", methods=["POST"])
def submit_hitl_action():
    """Handle human decision: approve_all, selective, steer, or reject."""
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        decision = data.get("decision", "approve_all")  # approve_all | selective | steer | reject
        approved_indices = data.get("approved_indices")
        feedback = data.get("feedback")
        req_cfg = get_llm_config_from_request(request)

        if not session_id:
            return jsonify({"success": False, "error": "session_id is required"}), 400

        graph = get_or_build_graph(session_id, req_cfg)
        config = {"configurable": {"thread_id": session_id}}
        current_state = dict(graph.get_state(config).values)

        if decision == "steer":
            # Re-synthesize with human feedback
            current_state["human_feedback"] = feedback or "Adjust retention strategy."
            cfg = REQUEST_LLM_CONFIGS.get(session_id, {})
            llm = get_llm(override_config=cfg)
            structured = llm.with_structured_output(RetentionProposal, method="function_calling", include_raw=True)
            prompt = f"""You are the Retention Supervisor. Revise your earlier proposal based on this mandatory directive:
DIRECTIVE: {current_state['human_feedback']}
TARGET: {current_state['customer_id']}
DIAGNOSTIC: {json.dumps(current_state.get('diagnostic_findings') or {}, indent=2)}
FINANCIAL: {json.dumps(current_state.get('financial_assessment') or {}, indent=2)}"""
            resp = structured.invoke(prompt)
            new_proposal: RetentionProposal = resp["parsed"]
            current_state["proposal"] = new_proposal.model_dump()
            graph.update_state(config, {"proposal": new_proposal.model_dump(), "human_feedback": feedback})
            return jsonify({
                "success": True,
                "action": "steered",
                "proposal": new_proposal.model_dump(),
                "message": "Proposal successfully revised based on operator directive.",
                "state": current_state,
            })

        if decision == "approve_all":
            new_status = "APPROVED"
            indices = None
        elif decision == "selective":
            indices = approved_indices or []
            new_status = "APPROVED" if indices else "REJECTED"
        elif decision == "reject":
            new_status = "REJECTED"
            indices = []
        else:
            new_status = "APPROVED"
            indices = None

        graph.update_state(config, {
            "hitl_status": new_status,
            "approved_action_indices": indices,
            "human_feedback": feedback or f"Decision: {decision}",
        })

        final_state = graph.invoke(None, config=config)
        return jsonify({
            "success": True,
            "decision": decision,
            "hitl_status": new_status,
            "execution_logs": final_state.get("execution_logs", []),
            "token_usage": final_state.get("token_usage", {}),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@menu09_bp.route("/api/tier09/audit", methods=["GET"])
def get_audit_trail():
    """Retrieve persisted operational execution logs."""
    try:
        if AUDIT_FILE.exists():
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
            return jsonify({"success": True, "total_logs": len(logs), "logs": logs})
        return jsonify({"success": True, "total_logs": 0, "logs": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
