import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
import time
import joblib
import pandas as pd
from dotenv import load_dotenv
# Ensure src directory is available in sys.path
SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
load_dotenv(ROOT / ".env")

from graph import build_retention_graph, synthesizer_node
from schema import (
    AgentState,
    DiagnosticFindings,
    ExecutionLogItem,
    FinancialAssessment,
    RetentionProposal,
    TokenUsage,
)

TARGET_CSV = ROOT / "data" / "target_customers.csv"
PLAYBOOK_CSV = ROOT / "data" / "retention_playbook.csv"
TICKETS_JSON = ROOT / "data" / "support_tickets.json"
FINANCIALS_JSON = ROOT / "data" / "accounts_financials.json"
MODEL_PATH = ROOT / "models" / "churn_model.joblib"


def load_dataset_records(customer_name: str) -> dict[str, Any]:
    """Load customer metrics, financial profile, tickets, and playbook."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at '{MODEL_PATH}'. Run 'python src/train.py' first."
        )

    model = joblib.load(MODEL_PATH)
    targets_df = pd.read_csv(TARGET_CSV)
    row = targets_df[targets_df["customer"].str.lower() == customer_name.lower()]
    if row.empty:
        raise ValueError(
            f"Customer '{customer_name}' not found in {TARGET_CSV}. "
            f"Available: {list(targets_df['customer'].values)}"
        )
    target_row = row.iloc[0]

    # 1. Tabular ML Churn Prediction
    feats = pd.DataFrame([{
        "transactions": target_row["transactions"],
        "active_days": target_row["active_days"],
        "inactive_days": target_row["inactive_days"],
    }])
    churn_prob = float(model.predict_proba(feats)[0][1])

    if churn_prob < 0.20:
        ml_key = "NO RISK"
        risk_level = "NO RISK"
    elif churn_prob < 0.50:
        ml_key = "LOW"
        risk_level = "LOW RISK"
    elif churn_prob < 0.75:
        ml_key = "MEDIUM"
        risk_level = "MEDIUM RISK"
    else:
        ml_key = "HIGH"
        risk_level = "HIGH RISK"

    # 2. Support Tickets
    all_tickets = []
    if TICKETS_JSON.exists():
        with open(TICKETS_JSON, "r", encoding="utf-8") as f:
            raw_tickets = json.load(f)
            all_tickets = [
                t for t in raw_tickets
                if t.get("customer", "").lower() == customer_name.lower()
            ]

    # 3. Financial Profile
    financials = {}
    if FINANCIALS_JSON.exists():
        with open(FINANCIALS_JSON, "r", encoding="utf-8") as f:
            all_fin = json.load(f)
            for k, v in all_fin.items():
                if k.lower() == customer_name.lower():
                    financials = v
                    break

    # 4. Baseline Playbook
    playbook_df = pd.read_csv(PLAYBOOK_CSV)
    pb_match = playbook_df[playbook_df["risk_level"].str.upper() == ml_key]
    if not pb_match.empty:
        pb_row = pb_match.iloc[0]
        actions_list = [a.strip() for a in str(pb_row.get("actions", "")).split(";") if a.strip()]
        sop_baseline = {
            "risk_level": ml_key,
            "sla": pb_row.get("sla", "48h"),
            "pic": pb_row.get("pic", "Account Manager"),
            "generic_incentive": pb_row.get("incentive", "None"),
            "generic_actions": actions_list,
        }
    else:
        sop_baseline = {
            "risk_level": ml_key,
            "sla": "48h",
            "pic": "Account Manager",
            "generic_incentive": "None",
            "generic_actions": [],
        }

    return {
        "customer_id": target_row["customer"],
        "transactions": int(target_row["transactions"]),
        "active_days": int(target_row["active_days"]),
        "inactive_days": int(target_row["inactive_days"]),
        "churn_probability": churn_prob,
        "ml_risk_level": risk_level,
        "support_tickets": all_tickets,
        "financials": financials,
        "sop_baseline": sop_baseline,
        "diagnostic_findings": None,
        "financial_assessment": None,
        "proposal": None,
        "hitl_status": "PENDING_REVIEW",
        "human_feedback": None,
        "execution_logs": [],
        "token_usage": TokenUsage(),
    }


def print_scorecard(state: dict[str, Any]) -> None:
    """Print executive terminal scorecard of multi-agent retention negotiation."""
    border = "=" * 80
    sub_border = "-" * 80

    cust = state["customer_id"]
    print(f"\n{border}")
    print(f"  TIER 09: MULTI-AGENT RETENTION GRAPH (HITL GATE) — {cust.upper()}")
    print(f"{border}")

    # 1. Tabular ML
    print("  [1] TABULAR ML PREDICTION (Scikit-Learn Baseline)")
    print(f"      • Calibrated Churn Probability : {state['churn_probability']:.1%}")
    print(f"      • Statistical Risk Level       : [{state['ml_risk_level']}]")
    print(
        f"      • Activity Signals             : {state['transactions']} txs | "
        f"{state['active_days']} active days | {state['inactive_days']} inactive days"
    )

    # 2. Diagnostic Specialist
    raw_diag = state.get("diagnostic_findings")
    diag = DiagnosticFindings.model_validate(raw_diag) if raw_diag else None
    print(f"\n{sub_border}")
    print("  [2] TECHNICAL / DIAGNOSTICS SPECIALIST REPORT")
    if diag:
        print(f"      • Primary Root Cause           : {diag.root_cause}")
        print(f"      • Technical Severity           : [{diag.technical_severity}]")
        print(f"      • Key Operational Blocker      : {diag.key_blocker}")
        print(f"      • Requires DevOps Escalation   : {'YES' if diag.requires_technical_escalation else 'NO'}")
        print(f"      • Diagnostic Analysis          : {diag.diagnostic_summary}")
    else:
        print("      • (No diagnostic data available)")

    # 3. Commercial / Finance Specialist
    raw_fin = state.get("financial_assessment")
    fin = FinancialAssessment.model_validate(raw_fin) if raw_fin else None
    print(f"\n{sub_border}")
    print("  [3] COMMERCIAL & FINANCE SPECIALIST REPORT")
    if fin:
        print(f"      • Account Tier                 : {fin.customer_tier}")
        print(f"      • Monthly GMV                  : Rp {fin.monthly_gmv_idr:,.0f}")
        print(f"      • Platform Monthly Revenue     : Rp {fin.monthly_revenue_idr:,.0f}")
        print(f"      • Held / Pending Payout        : Rp {fin.pending_payout_idr:,.0f}")
        print(f"      • Financial Exposure Verdict   : [{fin.financial_risk_verdict}]")
        print(f"      • Approved Retention Budget Cap: Rp {fin.approved_budget_cap_idr:,.0f}")
        print(f"      • Commercial Rationale         : {fin.commercial_rationale}")
    else:
        print("      • (No financial data available)")

    # 4. Supervisor's Negotiated Proposal
    raw_prop = state.get("proposal")
    prop = RetentionProposal.model_validate(raw_prop) if raw_prop else None
    print(f"\n{sub_border}")
    print("  [4] RETENTION LEAD / SUPERVISOR NEGOTIATED PROPOSAL")
    if prop:
        print(f"      • Executive Summary            : {prop.summary}")
        print(f"      • Harmonized Root Cause        : {prop.primary_root_cause}")
        print(f"      • SOP Status                   : {'OVERRIDDEN' if prop.is_override_sop else 'STANDARD ADEQUATE'}")
        if prop.is_override_sop:
            print(f"      • Override Justification       : {prop.override_reason}")
        print(f"      • Total Financial Impact       : Rp {prop.total_proposed_cost_idr:,.0f}")
        print("      • Negotiated Action Items      :")
        for idx, act in enumerate(prop.action_items, 1):
            approval_tag = "[REQUIRES HITL SIGN-OFF]" if act.requires_human_approval else "[AUTO-PERMITTED]"
            cost_str = f" | Cost/Waiver: Rp {act.cost_idr:,.0f}" if act.cost_idr > 0 else ""
            print(f"        {idx}. [{act.action_type}] {act.title} {approval_tag}{cost_str}")
            print(f"           Owner: {act.owner_role} | {act.description}")
    else:
        print("      • (No proposal synthesized)")

    # 5. HITL Status
    hitl_status = state.get("hitl_status")
    print(f"\n{sub_border}")
    print(f"  [5] SAFETY INTERCEPTOR: HUMAN-IN-THE-LOOP (HITL) GATE")
    if prop and prop.requires_hitl:
        print(f"      • Trigger Condition            : HITL REQUIRED ({prop.hitl_reason})")
        print(f"      • Gate Current Status          : [{hitl_status}]")
    else:
        print(f"      • Trigger Condition            : Low Risk / Standard Cost -> Safe for Auto-Approval")
        print(f"      • Gate Current Status          : [{hitl_status}]")
    print(f"{border}\n")


def print_execution_audit(state: dict[str, Any]) -> None:
    """Print final execution audit log with live simulated progress and token consumption."""
    border = "=" * 80
    sub_border = "-" * 80

    print(f"{border}")
    print("  [6] OPERATIONAL SIDE-EFFECTS DISPATCH AUDIT TRAIL (LIVE INTEGRATION)")
    print(f"{border}")
    raw_logs = state.get("execution_logs") or []
    logs = [
        ExecutionLogItem.model_validate(l) if isinstance(l, dict) else l
        for l in raw_logs
    ]
    if logs:
        print(f"  Executing {len(logs)} operational directives across enterprise systems...\n")
        for idx, log in enumerate(logs, 1):
            time.sleep(0.2)
            if log.status == "DISPATCHED":
                icon = "🚀 [DISPATCHED]"
            elif log.status == "SKIPPED":
                icon = "⏭️  [SKIPPED]"
            else:
                icon = "🛑 [BLOCKED]"

            print(f"  {idx}. {icon} [{log.action_type}] ──▶ {log.target_system}")
            print(f"     Payload : {json.dumps(log.payload, ensure_ascii=False)}")
            print(f"     Outcome : {log.message}\n")

        # Save audit file to data/execution_audit.json
        audit_path = ROOT / "data" / "execution_audit.json"
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump([l.model_dump() for l in logs], f, indent=2, ensure_ascii=False)
        print(f"  💾 Operational audit log persisted to: {audit_path}\n")
    else:
        print("  • (No operational actions were dispatched)\n")

    # Token Economics
    raw_tokens = state.get("token_usage")
    tokens = TokenUsage.model_validate(raw_tokens) if raw_tokens else TokenUsage()
    print(f"{sub_border}")
    print("  [7] MULTI-AGENT TOKEN ECONOMICS & PIPELINE RESOURCE USAGE")
    print(f"      • Diagnostic Specialist Tokens : Prompt + Completion Tracked")
    print(f"      • Financial Specialist Tokens  : Prompt + Completion Tracked")
    print(f"      • Retention Supervisor Tokens  : Prompt + Completion Tracked")
    print(f"      • Cumulative Token Usage       : {tokens.total_tokens:,} tokens "
          f"({tokens.prompt_tokens:,} prompt, {tokens.completion_tokens:,} completion)")
    print(f"{border}\n")


def run_pipeline(
    customer_name: str,
    auto_approve: bool = False,
    reject: bool = False,
    feedback: str | None = None,
) -> dict[str, Any]:
    """Execute the multi-agent retention state graph with HITL checkpoint and interactive controls."""
    init_state = load_dataset_records(customer_name)
    graph = build_retention_graph()

    thread_id = f"retention-{customer_name.replace(' ', '-').lower()}"
    config = {"configurable": {"thread_id": thread_id}}

    # Phase 1: Stream graph until hitl_gate interrupt
    print(f"\n[LangGraph] Initiating multi-agent retention deliberation for '{customer_name}'...")
    print("  ⏳ [1/3] Technical Specialist is diagnosing root causes & support tickets...")

    current_state = dict(init_state)
    for event in graph.stream(init_state, config=config):
        for node_name, node_output in event.items():
            current_state.update(node_output)
            if node_name == "diagnose":
                diag_obj = DiagnosticFindings.model_validate(node_output["diagnostic_findings"])
                print(f"  ✅ [1/3] Technical Specialist finished: {diag_obj.root_cause} [{diag_obj.technical_severity}]")
                print("  ⏳ [2/3] Commercial & Finance Specialist is calculating GMV, margins & budget caps...")
            elif node_name == "finance":
                fin_obj = FinancialAssessment.model_validate(node_output["financial_assessment"])
                print(f"  ✅ [2/3] Finance Specialist finished: {fin_obj.financial_risk_verdict}, Budget Cap: Rp {fin_obj.approved_budget_cap_idr:,.0f}")
                print("  ⏳ [3/3] Retention Lead / Supervisor is synthesizing negotiated plan...")
            elif node_name == "synthesizer":
                prop_obj = RetentionProposal.model_validate(node_output["proposal"])
                print(f"  ✅ [3/3] Retention Lead finished: {len(prop_obj.action_items)} action items (Total Cost: Rp {prop_obj.total_proposed_cost_idr:,.0f})")
            elif node_name == "hitl_gate":
                print("  🛡️  [HITL Gate] Safety policy evaluation complete.\n")

    # Display findings and proposal scorecard
    print_scorecard(current_state)

    # Phase 2: Checkpoint inspection & Human-in-the-Loop decision
    raw_prop = current_state.get("proposal")
    proposal = RetentionProposal.model_validate(raw_prop) if raw_prop else None
    hitl_status = current_state.get("hitl_status")
    approved_indices: list[int] | None = None
    actual_feedback = feedback

    if hitl_status == "PENDING_REVIEW":
        print("  ⚠️  ACTION REQUIRED: This retention proposal requires human authorization before execution.")

        if auto_approve:
            print("  [HITL Gate] --auto-approve flag detected. Proceeding with AUTOMATIC APPROVAL.")
            new_status = "APPROVED"
            actual_feedback = actual_feedback or "Auto-approved via CLI flag."
        elif reject:
            print("  [HITL Gate] --reject flag detected. Proceeding with REJECTION.")
            new_status = "REJECTED"
            actual_feedback = actual_feedback or "Rejected via CLI flag."
        else:
            # Interactive Menu Loop
            while True:
                print("\n  ╭──────────────────────────────────────────────────────────────────────────╮")
                print("  │ HUMAN-IN-THE-LOOP (HITL) OPERATIONAL CONTROL MENU                        │")
                print("  ├──────────────────────────────────────────────────────────────────────────┤")
                print("  │ [1] ✅ Approve All Actions & Dispatch to Target Systems                  │")
                print("  │ [2] 🔍 Interactive Item-by-Item Review (Toggle specific actions)         │")
                print("  │ [3] 💬 Steer / Revise Plan (Send guidance to Supervisor Agent to revise) │")
                print("  │ [4] ❌ Reject Proposal Entirely (Block all side-effects)                 │")
                print("  ╰──────────────────────────────────────────────────────────────────────────╯")

                try:
                    choice = input("  Select action [1/2/3/4] (default: 1): ").strip()
                except (EOFError, KeyboardInterrupt):
                    choice = "4"

                if not choice or choice == "1":
                    new_status = "APPROVED"
                    actual_feedback = actual_feedback or "Approved in full by operator."
                    approved_indices = None
                    print("  ✅ All proposed actions marked as APPROVED.")
                    break

                elif choice == "2":
                    # Item-by-item selective review
                    print("\n  ─── Interactive Item-by-Item Review ───")
                    approved_indices = []
                    for idx, act in enumerate(proposal.action_items):
                        cost_str = f" | Value: Rp {act.cost_idr:,.0f}" if act.cost_idr > 0 else ""
                        print(f"\n  [{idx+1}/{len(proposal.action_items)}] [{act.action_type}] {act.title}{cost_str}")
                        print(f"      Owner: {act.owner_role}")
                        print(f"      Details: {act.description}")
                        try:
                            ans = input(f"      -> Authorize this action? ([y]es / [n]o) [y]: ").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            ans = "n"

                        if ans in ("", "y", "yes"):
                            approved_indices.append(idx)
                            print(f"      ✅ Action {idx+1} APPROVED.")
                        else:
                            print(f"      ⏭️  Action {idx+1} EXCLUDED / OMITTED.")

                    if approved_indices:
                        new_status = "APPROVED"
                        actual_feedback = f"Selectively approved {len(approved_indices)} of {len(proposal.action_items)} actions."
                        print(f"\n  ✅ Selective review complete: {len(approved_indices)} of {len(proposal.action_items)} actions authorized.")
                    else:
                        new_status = "REJECTED"
                        actual_feedback = "All individual actions were omitted by operator."
                        print("\n  ❌ All actions omitted. Proposal marked as REJECTED.")
                    break

                elif choice == "3":
                    # Human Steering / Plan Revision
                    try:
                        steering_prompt = input("\n  Enter steering directive for Supervisor Agent:\n  > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        steering_prompt = ""

                    if not steering_prompt:
                        print("  (No steering directive entered, returning to menu)")
                        continue

                    print(f"\n  🧠 Supervisor Agent is re-evaluating retention plan with your feedback:")
                    print(f"     \"{steering_prompt}\"...")
                    current_state["human_feedback"] = steering_prompt
                    synth_result = synthesizer_node(current_state)
                    current_state["proposal"] = synth_result["proposal"]
                    current_state["token_usage"] = synth_result["token_usage"]
                    raw_prop = current_state["proposal"]
                    proposal = RetentionProposal.model_validate(raw_prop)
                    print("  ✨ Revised proposal generated successfully!")
                    print_scorecard(current_state)
                    # Loop back to menu so operator can review revised proposal
                    continue

                elif choice == "4":
                    new_status = "REJECTED"
                    actual_feedback = actual_feedback or "Rejected in full by operator."
                    approved_indices = []
                    print("  ❌ Entire retention proposal marked as REJECTED.")
                    break
                else:
                    print("  Invalid selection. Please choose 1, 2, 3, or 4.")

        # Update state in checkpoint
        update_payload = {
            "hitl_status": new_status,
            "human_feedback": actual_feedback,
            "approved_action_indices": approved_indices,
            "proposal": current_state.get("proposal"),
        }
        graph.update_state(config, update_payload)

        # Resume graph execution from hitl_gate -> execution_node -> END
        print(f"\n[LangGraph] Resuming execution pipeline from checkpoint ({new_status})...")
        final_state = graph.invoke(None, config=config)
    else:
        # Auto-approved: resume to execute routine side effects
        print("  ✨ Routine/Low-Risk Action Plan. Auto-approving and executing...")
        graph.update_state(config, {"hitl_status": "AUTO_APPROVED", "approved_action_indices": None})
        final_state = graph.invoke(None, config=config)

    # Print execution audit
    print_execution_audit(final_state)
    return final_state


def main():
    parser = argparse.ArgumentParser(
        description="Tier 09: Multi-Agent Retention State Graph with Human-in-the-Loop (HITL)"
    )
    parser.add_argument(
        "--id",
        type=str,
        default="Store Critical",
        help="Target customer name (e.g. 'Store Critical', 'Store Watchlist', 'Store Safe')",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve the HITL gate without interactive terminal pause",
    )
    parser.add_argument(
        "--reject",
        action="store_true",
        help="Automatically reject the proposal at the HITL gate",
    )
    parser.add_argument(
        "--feedback",
        type=str,
        default=None,
        help="Optional human feedback string to attach to decision",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run evaluation sequentially across all target accounts",
    )
    args = parser.parse_args()

    if args.all:
        targets_df = pd.read_csv(TARGET_CSV)
        for name in targets_df["customer"].values:
            run_pipeline(name, auto_approve=args.auto_approve, reject=args.reject, feedback=args.feedback)
    else:
        run_pipeline(args.id, auto_approve=args.auto_approve, reject=args.reject, feedback=args.feedback)


if __name__ == "__main__":
    main()
