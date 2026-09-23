import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from llm import get_llm
from tools import (
    get_retention_playbook,
    get_target_customers,
    list_customers,
    predict_churn_risk,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# ==============================================================================
# 1. TOOL REGISTRY
# ==============================================================================
tools = [get_target_customers, list_customers, predict_churn_risk, get_retention_playbook]
tools_by_name = {tool.name: tool for tool in tools}

# ==============================================================================
# 2. LLM INITIALIZATION & TOOL BINDING
# ==============================================================================
llm = get_llm()
llm_with_tools = llm.bind_tools(tools)

# ==============================================================================
# 3. AGENT SYSTEM PROMPT
# ==============================================================================
SYSTEM_PROMPT = """You are a Senior Customer Success and Retention Strategist.
Your task: Analyze customer churn risk for merchants and prescribe concrete action plans from the company's retention playbook.

TOOL USAGE RULES:
1. When asked to evaluate target accounts or when no specific merchant is named, call `get_target_customers` to inspect data/target_customers.csv.
2. Always call `predict_churn_risk` to retrieve the Scikit-Learn churn probability and risk tier for each merchant evaluated.
3. The model classifies risk into four tiers: 'NO RISK', 'LOW', 'MEDIUM', and 'HIGH'. Call `get_retention_playbook` to retrieve the official SOP (SLA, account owner, incentive, and action steps) for that tier.
4. If a merchant is not found in target accounts, call `list_customers` to check the historical database.

OUTPUT GUIDELINES (CLI TERMINAL COMPATIBLE):
- Tone: Direct, concise, analytical, and operational.
- Do NOT use bold markdown (**text**) or markdown tables (|---|) as they clutter terminal displays.
- Use plain-text formatting with neat indentation and simple bullet points (-).
- Avoid markdown header tags (### or ####). Use plain capitalized headings and simple dividers (such as ────).
- Explicitly emphasize that ML predictions serve as early warning indicators rather than deterministic verdicts.
"""


# ==============================================================================
# 4. RUNNER: AUTONOMOUS AGENT LOOP
# ==============================================================================
def format_cli_output(text: str) -> str:
    """Strip bold markdown tags and format headers for clean terminal output."""
    cleaned = text.replace("**", "").replace("### ", "- ").replace("## ", "- ").replace("# ", "")
    return cleaned.strip()


def run_agent(user_query: str):
    provider_name = os.getenv("AI_PROVIDER", "gemini").upper()
    border = "=" * 68
    print(f"\n{border}")
    print(f"  CUSTOMER RETENTION AGENT [{provider_name}]")
    print(f"{border}")
    print(f"  Query: \"{user_query}\"\n")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query),
    ]
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    step = 1
    max_steps = 6

    while step <= max_steps:
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        # Accumulate token usage across agentic reasoning steps
        if hasattr(ai_msg, "usage_metadata") and ai_msg.usage_metadata:
            prompt_tokens += ai_msg.usage_metadata.get("input_tokens", 0) or 0
            completion_tokens += ai_msg.usage_metadata.get("output_tokens", 0) or 0
            total_tokens += ai_msg.usage_metadata.get("total_tokens", 0) or 0
        elif hasattr(ai_msg, "response_metadata") and ai_msg.response_metadata:
            raw_usage = (
                ai_msg.response_metadata.get("token_usage")
                or ai_msg.response_metadata.get("usage")
                or {}
            )
            p = raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens", 0) or 0
            c = raw_usage.get("completion_tokens") or raw_usage.get("output_tokens", 0) or 0
            prompt_tokens += p
            completion_tokens += c
            total_tokens += (p + c)

        # Agent completed tool reasoning and produced final response
        if not ai_msg.tool_calls:
            raw_content = ""
            if isinstance(ai_msg.content, list):
                text_parts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in ai_msg.content]
                raw_content = "".join(text_parts)
            else:
                raw_content = str(ai_msg.content)

            print(f"\n{border}")
            print("  RETENTION ANALYSIS & ACTION PLAN")
            print(f"{border}\n")
            if total_tokens == 0 and (prompt_tokens > 0 or completion_tokens > 0):
                total_tokens = prompt_tokens + completion_tokens

            print(format_cli_output(raw_content))
            print(f"\n{border}")
            print(f"  Cumulative Token Usage ({step} reasoning turns):")
            print(f"  Prompt = {prompt_tokens:,} | Completion = {completion_tokens:,} | Total = {total_tokens:,}")
            print(f"{border}\n")
            return

        # Execute tools requested by the model
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool:
                print(f"  -> [Step {step}] Invoking tool: {tool_name} {tool_args}")
                tool_output = selected_tool.invoke(tool_args)
            else:
                tool_output = f"Error: Tool '{tool_name}' was not found in registry."

            first_line = str(tool_output).split("\n")[0].strip()
            print(f"     Output: {first_line}")
            messages.append(
                ToolMessage(
                    content=str(tool_output),
                    tool_call_id=tool_call["id"],
                )
            )

        step += 1

    print("\n[WARNING] Maximum execution step limit reached before final response.")


if __name__ == "__main__":
    default_question = (
        "Evaluate all target merchants in data/target_customers.csv. "
        "Predict their churn risk using the ML model, analyze risk drivers, "
        "and prescribe retention playbook SOP actions for accounts at risk."
    )

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_question
    run_agent(query)
