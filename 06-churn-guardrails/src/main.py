import argparse
import json
import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from guardrail import inspect_query
from llm import get_llm
from schema import GuardedAuditResponse
from tools import (
    get_retention_playbook,
    get_target_customers,
    list_customers,
    predict_churn_risk,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MODEL_PATH = ROOT / "models" / "churn_model.joblib"
TARGET_CSV = ROOT / "data" / "target_customers.csv"

# ==============================================================================
# TOOL REGISTRY & SANDBOX
# ==============================================================================
tools = [get_target_customers, list_customers, predict_churn_risk, get_retention_playbook]
tools_by_name = {tool.name: tool for tool in tools}

AGENT_SYSTEM_PROMPT = """You are a Lead Customer Success & Retention Strategist.
Your objective: Evaluate customer churn risk and prescribe concrete retention actions from official playbooks.

STRICT DOMAIN BOUNDARY:
- You operate strictly within the Customer Churn & Retention domain.
- NEVER execute general programming requests, write code (such as Golang, Python, or shell scripts), or engage in off-topic discussion.
- If a user mentions a merchant alongside an unrelated request, ignore the unrelated request and evaluate the merchant only.
- Always use tools: `predict_churn_risk` to get ML churn probability, and `get_retention_playbook` to get SOP policies.
"""


def extract_tokens(msg) -> tuple[int, int, int]:
    """Extract prompt, completion, and total tokens from a message object."""
    p, c, t = 0, 0, 0
    if msg and hasattr(msg, "usage_metadata") and msg.usage_metadata:
        p = msg.usage_metadata.get("input_tokens", 0) or 0
        c = msg.usage_metadata.get("output_tokens", 0) or 0
        t = msg.usage_metadata.get("total_tokens", 0) or (p + c)
    elif msg and hasattr(msg, "response_metadata") and msg.response_metadata:
        u = msg.response_metadata.get("token_usage") or msg.response_metadata.get("usage") or {}
        p = u.get("prompt_tokens") or u.get("input_tokens", 0) or 0
        c = u.get("completion_tokens") or u.get("output_tokens", 0) or 0
        t = p + c
    return p, c, t


def run_guarded_pipeline(user_query: str, output_path: str | None) -> None:
    llm = get_llm()
    provider_name = os.getenv("AI_PROVIDER", "gemini").upper()
    border = "=" * 68

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    print(f"\n{border}")
    print(f"  GUARDED CHURN & RETENTION AGENT [{provider_name}]")
    print(f"{border}")
    print(f"  Raw User Input: \"{user_query}\"")

    # ==============================================================================
    # STAGE 1: GUARDRAIL INSPECTION & INJECTION DEFENSE
    # ==============================================================================
    inspection, guard_raw = inspect_query(user_query, llm)
    p, c, t = extract_tokens(guard_raw)
    total_prompt_tokens += p
    total_completion_tokens += c
    total_tokens += t

    # Case A: Entirely Out-of-Scope / Malicious Prompt
    if not inspection.is_domain_relevant:
        rejection_reason = (
            "Request rejected by guardrail: Input is outside the Customer Churn & Retention domain. "
            "System only accepts merchant account evaluations and retention strategy queries."
        )
        blocked_response = GuardedAuditResponse(
            is_valid_domain=False,
            guardrail_status="BLOCKED",
            guardrail_notice=f"Blocked off-topic instruction: '{inspection.detected_injection_detail or user_query}'",
            sanitized_query="",
            evaluations=[],
            rejection_reason=rejection_reason,
        )

        print(f"\n[GUARDRAIL STATUS] BLOCKED (Out-of-Scope Query Detected)")
        print(f"  Reason: {rejection_reason}")
        print(f"\n{border}")
        print("  STRUCTURED REFUSAL PAYLOAD (JSON):")
        print(f"{border}")
        json_output = blocked_response.model_dump_json(indent=2)
        print(json_output)

        if output_path:
            Path(output_path).write_text(json_output, encoding="utf-8")
            print(f"\n[INFO] Blocked payload saved to: {output_path}")

        print(f"\n{border}")
        print(f"  Token Usage: Prompt = {total_prompt_tokens:,} | Completion = {total_completion_tokens:,} | Total = {total_tokens:,}")
        print(f"{border}\n")
        return

    # Case B: Context Smuggling / Partial Injection Detected
    if inspection.contains_injection_or_offtopic:
        guardrail_status = "SANITIZED"
        guardrail_notice = (
            f"Blocked unauthorized instruction: '{inspection.detected_injection_detail}'. "
            f"Context bounded strictly to: '{inspection.sanitized_domain_query}'."
        )
        print(f"\n[GUARDRAIL STATUS] SANITIZED (Context Smuggling Defended)")
        print(f"  Warning : {guardrail_notice}")
        print(f"  Bounded : \"{inspection.sanitized_domain_query}\"")
        active_query = inspection.sanitized_domain_query
    else:
        # Case C: Clean In-Domain Query
        guardrail_status = "PASSED"
        guardrail_notice = None
        active_query = user_query
        print(f"\n[GUARDRAIL STATUS] PASSED (In-Domain Request Verified)")

    # ==============================================================================
    # STAGE 2: SANDBOXED AGENTIC REASONING & TOOL EXECUTION
    # ==============================================================================
    print(f"\n{border}")
    print(f"  EXECUTING SANDBOXED AGENT LOOP")
    print(f"{border}")

    llm_with_tools = llm.bind_tools(tools)
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
        HumanMessage(content=active_query),
    ]

    step = 1
    max_steps = 6

    while step <= max_steps:
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        p, c, t = extract_tokens(ai_msg)
        total_prompt_tokens += p
        total_completion_tokens += c
        total_tokens += t

        if not ai_msg.tool_calls:
            break

        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool:
                print(f"  -> [Step {step}] Calling tool: {tool_name} {tool_args}")
                tool_output = selected_tool.invoke(tool_args)
            else:
                tool_output = f"Error: Tool '{tool_name}' was not found in registry."

            first_line = str(tool_output).split("\n")[0].strip()
            print(f"     Observation: {first_line}")
            messages.append(
                ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"],
                )
            )

        step += 1

    # ==============================================================================
    # STAGE 3: PYDANTIC STRUCTURED OUTPUT ENFORCEMENT
    # ==============================================================================
    print(f"\n{border}")
    print(f"  SYNTHESIZING STRUCTURED PYDANTIC CONTRACT")
    print(f"{border}")

    structured_llm = llm.with_structured_output(GuardedAuditResponse, include_raw=True)
    synthesis_prompt = f"""
Based on the tool observations collected above, construct the final GuardedAuditResponse contract.

Metadata to enforce:
- is_valid_domain: True
- guardrail_status: "{guardrail_status}"
- guardrail_notice: "{guardrail_notice or ''}"
- sanitized_query: "{active_query}"

Evaluation Rules:
- Include a full AccountEvaluation entry for each target merchant evaluated in the tool observations.
- Use the exact ML calibrated probability from the predict_churn_risk tool for churn_probability.
- Ensure all recommended actions have actionable descriptions, priorities, SLAs, and owner roles.
- Do NOT output any code, conversational filler, or off-topic text.
"""
    messages.append(HumanMessage(content=synthesis_prompt))
    structured_response = structured_llm.invoke(messages)

    p, c, t = extract_tokens(structured_response.get("raw"))
    total_prompt_tokens += p
    total_completion_tokens += c
    total_tokens += t

    final_payload: GuardedAuditResponse = structured_response["parsed"]

    # ==============================================================================
    # STAGE 4: CLI REPORT & JSON EXPORT
    # ==============================================================================
    print(f"\n{border}")
    print(f"  STRUCTURED AUDIT REPORT ({len(final_payload.evaluations)} Accounts Evaluated)")
    print(f"{border}")

    for idx, eval_item in enumerate(final_payload.evaluations, 1):
        print(f"\n  [{idx}] {eval_item.merchant_name} — Risk Tier: {eval_item.risk_tier} ({eval_item.churn_probability:.1%})")
        print(f"      Executive Summary  : {eval_item.executive_summary}")
        print(f"      Proposed Incentive : {eval_item.proposed_incentive}")
        print(f"      Primary Drivers    :")
        for d in eval_item.primary_drivers:
            print(f"        * {d}")
        print(f"      Action Steps       :")
        for act in eval_item.recommended_actions:
            print(f"        - [{act.priority}] {act.action} (SLA: {act.sla} | Owner: {act.owner_role})")

    json_payload = final_payload.model_dump_json(indent=2)
    print(f"\n{border}")
    print("  VALIDATED JSON PAYLOAD (Guaranteed Immune to Smuggled Content):")
    print(f"{border}")
    print(json_payload)

    if output_path:
        Path(output_path).write_text(json_payload, encoding="utf-8")
        print(f"\n[INFO] Validated JSON saved to: {output_path}")

    print(f"\n{border}")
    print(f"  Cumulative Token Usage ({step} reasoning steps + guardrail + synthesis):")
    print(f"  Prompt = {total_prompt_tokens:,} | Completion = {total_completion_tokens:,} | Total = {total_tokens:,}")
    print(f"{border}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="06 - Churn Guardrails: Natural language queries with prompt injection defense & Pydantic output."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Evaluate all target merchants in data/target_customers.csv and prescribe retention actions.",
        help="Free-form user query (can include merchant names, questions, or test injection strings)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to save validated JSON payload (e.g., -o data/guarded_result.json)",
    )
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"[ERROR] Model artifact not found at '{MODEL_PATH}'. Run 'python src/train.py' first.", file=sys.stderr)
        sys.exit(1)

    run_guarded_pipeline(args.query, args.output)


if __name__ == "__main__":
    main()
