import json
from typing import Any
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from llm import extract_token_usage, get_llm
from schema import (
    AgentState,
    DiagnosticFindings,
    ExecutionLogItem,
    FinancialAssessment,
    RetentionProposal,
    TokenUsage,
)
from tools import execute_action

DIAGNOSTIC_SYSTEM_PROMPT = """You are the Lead Technical & Diagnostics Specialist in an enterprise merchant retention squad.
Your role:
1. Examine the merchant's tabular churn probability, activity metrics, and unstructured customer support tickets.
2. Pinpoint the primary qualitative root cause behind their churn risk.
3. Assess the technical severity of the blocker (e.g. CRITICAL_P1, HIGH_P2, NONE).
4. Identify if technical escalation (e.g. DevOps / Engineering intervention) is required.

Return a strictly validated DiagnosticFindings schema."""

FINANCIAL_SYSTEM_PROMPT = """You are the Head of Commercial Strategy & Finance in an enterprise merchant retention squad.
Your role:
1. Examine the merchant's financial metrics (Monthly GMV, Revenue, Margin %, Pending Payouts, Max Retention Budget).
2. Review the Technical Diagnostic Specialist's root-cause findings.
3. Evaluate financial exposure and risk to platform revenue.
4. Establish a strict approved budget ceiling for incentives/waivers to guarantee positive unit economics.
5. If there is a pending payout hold, evaluate whether unfreezing or expedited settlement is justified.

Return a strictly validated FinancialAssessment schema."""

SYNTHESIZER_SYSTEM_PROMPT = """You are the Senior Retention Director & Supervisor in an enterprise merchant retention squad.
Your role:
1. Review the Diagnostic Specialist's root-cause findings and the Finance Specialist's budget assessment.
2. Compare them against the generic standard SOP playbook.
3. Decide whether the standard SOP is adequate or if a specialized override is required (e.g., offering discounts to a merchant whose webhook is broken is counterproductive and damages trust).
4. Construct a concrete, prioritized RetentionProposal with atomic action items.
5. Determine if Human-in-the-Loop (HITL) review is mandatory (requires_hitl = True):
   - Set True if total cost > Rp 5.000.000, OR churn risk > 80%, OR plan involves P1 DevOps Escalation / Finance Payout Release.
   - Otherwise, routine low-risk actions can proceed automatically (requires_hitl = False).

Return a strictly validated RetentionProposal schema."""


def diagnose_node(state: AgentState) -> dict[str, Any]:
    """Diagnostic Specialist node: root cause and technical severity diagnosis."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(
        DiagnosticFindings, method="function_calling", include_raw=True
    )

    prompt = f"""{DIAGNOSTIC_SYSTEM_PROMPT}

TARGET MERCHANT: {state['customer_id']}
TABULAR ML METRICS:
- Calibrated Churn Probability : {state['churn_probability']:.1%}
- Statistical Risk Tier        : [{state['ml_risk_level']}]
- Activity                     : {state['transactions']} transactions | {state['active_days']} active days | {state['inactive_days']} inactive days

UNSTRUCTURED SUPPORT TICKETS & COMPLAINTS:
{json.dumps(state['support_tickets'], indent=2, ensure_ascii=False)}
"""

    resp = structured_llm.invoke(prompt)
    findings: DiagnosticFindings = resp["parsed"]
    tokens = extract_token_usage(resp.get("raw"))
    raw_tok = state.get("token_usage")
    current_tokens = TokenUsage.model_validate(raw_tok) if raw_tok else TokenUsage()

    return {
        "diagnostic_findings": findings.model_dump(),
        "token_usage": current_tokens.add(tokens).model_dump(),
    }


def finance_node(state: AgentState) -> dict[str, Any]:
    """Finance & Commercial Specialist node: business exposure and budget ceiling."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(
        FinancialAssessment, method="function_calling", include_raw=True
    )

    raw_diag = state.get("diagnostic_findings")
    if isinstance(raw_diag, dict):
        diag_summary = json.dumps(raw_diag, indent=2, ensure_ascii=False)
    elif hasattr(raw_diag, "model_dump_json"):
        diag_summary = raw_diag.model_dump_json(indent=2)
    else:
        diag_summary = "No diagnostic findings."

    prompt = f"""{FINANCIAL_SYSTEM_PROMPT}

TARGET MERCHANT: {state['customer_id']}
MERCHANT FINANCIAL PROFILE:
{json.dumps(state['financials'], indent=2, ensure_ascii=False)}

ML RISK STATUS:
- Churn Probability: {state['churn_probability']:.1%} [{state['ml_risk_level']}]

DIAGNOSTIC SPECIALIST REPORT:
{diag_summary}
"""

    resp = structured_llm.invoke(prompt)
    assessment: FinancialAssessment = resp["parsed"]
    tokens = extract_token_usage(resp.get("raw"))
    raw_tok = state.get("token_usage")
    current_tokens = TokenUsage.model_validate(raw_tok) if raw_tok else TokenUsage()

    return {
        "financial_assessment": assessment.model_dump(),
        "token_usage": current_tokens.add(tokens).model_dump(),
    }


def synthesizer_node(state: AgentState) -> dict[str, Any]:
    """Retention Lead / Supervisor node: balances tech and finance into an action proposal."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(
        RetentionProposal, method="function_calling", include_raw=True
    )

    raw_diag = state.get("diagnostic_findings")
    raw_fin = state.get("financial_assessment")
    diag_str = json.dumps(raw_diag, indent=2, ensure_ascii=False) if isinstance(raw_diag, dict) else (raw_diag.model_dump_json(indent=2) if hasattr(raw_diag, "model_dump_json") else "{}")
    fin_str = json.dumps(raw_fin, indent=2, ensure_ascii=False) if isinstance(raw_fin, dict) else (raw_fin.model_dump_json(indent=2) if hasattr(raw_fin, "model_dump_json") else "{}")
    human_feedback = state.get("human_feedback")
    steering_section = ""
    if human_feedback:
        steering_section = f"""
CRITICAL HUMAN OPERATOR STEERING INSTRUCTION:
The human retention supervisor / committee reviewed an earlier proposal and gave this mandatory directive:
"{human_feedback}"
You MUST strictly obey this directive in your updated proposal (e.g. adjust budget, remove/modify disallowed actions, or adjust strategy).
"""

    prompt = f"""{SYNTHESIZER_SYSTEM_PROMPT}

TARGET MERCHANT: {state['customer_id']}
ML CHURN PREDICTION: {state['churn_probability']:.1%} [{state['ml_risk_level']}]

GENERIC SOP PLAYBOOK BASELINE:
{json.dumps(state['sop_baseline'], indent=2, ensure_ascii=False)}

DIAGNOSTIC SPECIALIST REPORT:
{diag_str}

FINANCIAL & COMMERCIAL REPORT:
{fin_str}
{steering_section}
"""

    resp = structured_llm.invoke(prompt)
    proposal: RetentionProposal = resp["parsed"]
    tokens = extract_token_usage(resp.get("raw"))
    raw_tok = state.get("token_usage")
    current_tokens = TokenUsage.model_validate(raw_tok) if raw_tok else TokenUsage()

    return {
        "proposal": proposal.model_dump(),
        "token_usage": current_tokens.add(tokens).model_dump(),
    }


def hitl_gate_node(state: AgentState) -> dict[str, Any]:
    """Safety checkpoint node: flags high-impact plans for Human-in-the-Loop review."""
    raw_prop = state.get("proposal")
    if raw_prop:
        proposal = RetentionProposal.model_validate(raw_prop) if isinstance(raw_prop, dict) else raw_prop
        if proposal.requires_hitl:
            hitl_status = "PENDING_REVIEW"
        else:
            hitl_status = "AUTO_APPROVED"
    else:
        hitl_status = "AUTO_APPROVED"
    return {
        "hitl_status": hitl_status,
    }


def execution_node(state: AgentState) -> dict[str, Any]:
    """Action Dispatcher node: executes approved side-effects or records cancellation."""
    customer = state["customer_id"]
    status = state.get("hitl_status", "AUTO_APPROVED")
    logs: list[ExecutionLogItem] = list(state.get("execution_logs") or [])

    raw_prop = state.get("proposal")
    if not raw_prop:
        return {"execution_logs": logs}

    proposal = RetentionProposal.model_validate(raw_prop) if isinstance(raw_prop, dict) else raw_prop

    approved_indices = state.get("approved_action_indices")

    if status in ("APPROVED", "AUTO_APPROVED"):
        for idx, item in enumerate(proposal.action_items):
            if approved_indices is not None and idx not in approved_indices:
                logs.append(
                    ExecutionLogItem(
                        action_type=item.action_type,
                        target_system="Safety Interceptor",
                        payload={"action_title": item.title, "cost_idr": item.cost_idr},
                        status="SKIPPED",
                        message=f"Action '{item.title}' was skipped / omitted by operator during selective review.",
                    ).model_dump()
                )
            else:
                log_item = execute_action(item, customer)
                logs.append(log_item.model_dump())
    elif status == "REJECTED":
        feedback = state.get("human_feedback") or "Human operator declined proposal execution."
        logs.append(
            ExecutionLogItem(
                action_type="CANCELLED_BY_HUMAN",
                target_system="Safety Interceptor",
                payload={"proposal_summary": proposal.summary, "reason": feedback},
                status="BLOCKED",
                message=f"Retention proposal rejected by operator: {feedback}",
            ).model_dump()
        )

    return {"execution_logs": logs}


def build_retention_graph():
    """Build and compile the LangGraph StateGraph with MemorySaver and HITL checkpoint."""
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

    memory = MemorySaver()
    # Interrupt after hitl_gate to pause execution for human inspection
    graph = builder.compile(checkpointer=memory, interrupt_after=["hitl_gate"])
    return graph
