import argparse
import json
import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import pandas as pd
from dotenv import load_dotenv

from llm import get_llm
from schema import BatchChurnAssessment, ChurnAssessment

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MODEL_PATH = ROOT / "models" / "churn_model.joblib"
TARGET_CSV = ROOT / "data" / "target_customers.csv"


def extract_token_usage(raw_msg) -> tuple[int, int, int]:
    """Extract prompt, completion, and total tokens from raw response."""
    p, c, t = 0, 0, 0
    if raw_msg and hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
        p = raw_msg.usage_metadata.get("input_tokens", 0) or 0
        c = raw_msg.usage_metadata.get("output_tokens", 0) or 0
        t = raw_msg.usage_metadata.get("total_tokens", 0) or (p + c)
    elif raw_msg and hasattr(raw_msg, "response_metadata") and raw_msg.response_metadata:
        u = raw_msg.response_metadata.get("token_usage") or raw_msg.response_metadata.get("usage") or {}
        p = u.get("prompt_tokens") or u.get("input_tokens", 0) or 0
        c = u.get("completion_tokens") or u.get("output_tokens", 0) or 0
        t = p + c
    return p, c, t


def evaluate_single(model, customer: dict, llm, output_path: str | None) -> None:
    """Evaluate a single merchant account using ChurnAssessment schema."""
    features = ["transactions", "active_days", "inactive_days"]
    input_df = pd.DataFrame([customer])[features]
    ml_prob = float(model.predict_proba(input_df)[0][1])

    stat_tier = "HIGH" if ml_prob >= 0.70 else "MEDIUM" if ml_prob >= 0.40 else "LOW" if ml_prob >= 0.10 else "NO RISK"

    context = f"""
Merchant Account: {customer["customer"]}
Total Transactions: {customer["transactions"]}
Active Days: {customer["active_days"]}
Inactive Days: {customer["inactive_days"]}
ML Calibrated Churn Probability: {ml_prob:.1%}
Statistical Risk Tier: {stat_tier}
"""

    prompt = f"""
You are a Lead Customer Success Strategist. Evaluate the following account and construct a type-safe operational retention plan.

Account Activity Data:
{context}

Instructions:
- Fill out all schema fields accurately.
- Use the provided ML calibrated probability ({ml_prob:.3f}) for the churn_probability field.
- Ensure risk_tier aligns with the ML probability and behavioral drivers.
- Prescribe concrete, prioritized ActionItems with specific SLA windows and internal owner roles.
"""

    structured_llm = llm.with_structured_output(ChurnAssessment, include_raw=True)
    raw_response = structured_llm.invoke(prompt)

    assessment: ChurnAssessment = raw_response["parsed"]
    p, c, t = extract_token_usage(raw_response.get("raw"))

    provider_name = os.getenv("AI_PROVIDER", "gemini").upper()
    border = "=" * 64

    print(f"\n{border}")
    print(f"  STRUCTURED CHURN ASSESSMENT: {assessment.merchant_name} [{provider_name}]")
    print(f"{border}")
    print(f"  Risk Tier          : {assessment.risk_tier}")
    print(f"  Churn Probability  : {assessment.churn_probability:.1%}")
    print(f"  Executive Summary  : {assessment.executive_summary}")
    print(f"  Proposed Incentive : {assessment.proposed_incentive}")
    print("\n  Primary Risk Drivers:")
    for driver in assessment.primary_drivers:
        print(f"    - {driver}")

    print("\n  Recommended Operational Actions:")
    for idx, item in enumerate(assessment.recommended_actions, 1):
        print(f"    {idx}. [{item.priority}] {item.action}")
        print(f"       SLA: {item.sla} | Owner: {item.owner_role}")

    json_payload = assessment.model_dump_json(indent=2)
    print(f"\n{border}")
    print("  VALIDATED JSON PAYLOAD (Ready for API / DB persistence):")
    print(f"{border}")
    print(json_payload)

    if output_path:
        Path(output_path).write_text(json_payload, encoding="utf-8")
        print(f"\n[INFO] Validated JSON saved to: {output_path}")

    print(f"\n{border}")
    print(f"  Token Usage: Prompt = {p:,} | Completion = {c:,} | Total = {t:,}")
    print(f"{border}\n")


def evaluate_batch(model, df: pd.DataFrame, llm, output_path: str | None) -> None:
    """Evaluate all merchant accounts in batch using BatchChurnAssessment schema."""
    features = ["transactions", "active_days", "inactive_days"]
    probabilities = model.predict_proba(df[features])[:, 1]

    accounts_context = []
    for idx, row in df.iterrows():
        p = float(probabilities[idx])
        tier = "HIGH" if p >= 0.70 else "MEDIUM" if p >= 0.40 else "LOW" if p >= 0.10 else "NO RISK"
        accounts_context.append(
            f"Account #{idx+1}: {row['customer']} | Transactions: {row['transactions']} | "
            f"Active: {row['active_days']} days | Inactive: {row['inactive_days']} days | "
            f"ML Calibrated Churn Probability: {p:.1%} (Tier: {tier})"
        )

    context_str = "\n".join(accounts_context)
    prompt = f"""
You are a Lead Customer Success Strategist. Evaluate the following {len(df)} target merchant accounts in batch and construct a type-safe operational retention plan for EACH merchant.

Target Merchant Accounts:
{context_str}

Instructions:
- Provide a valid ChurnAssessment entry for EVERY merchant in the list.
- Use the exact ML calibrated probability provided in each account entry for churn_probability.
- Prescribe concrete, prioritized ActionItems with specific SLA windows and internal owner roles.
"""

    structured_llm = llm.with_structured_output(BatchChurnAssessment, include_raw=True)
    raw_response = structured_llm.invoke(prompt)

    batch_result: BatchChurnAssessment = raw_response["parsed"]
    p, c, t = extract_token_usage(raw_response.get("raw"))

    provider_name = os.getenv("AI_PROVIDER", "gemini").upper()
    border = "=" * 68

    print(f"\n{border}")
    print(f"  BATCH STRUCTURED CHURN ASSESSMENT ({len(batch_result.assessments)} ACCOUNTS) [{provider_name}]")
    print(f"{border}")

    # Summary table
    print(f"\n  {'MERCHANT':<18} | {'TIER':<9} | {'PROBABILITY':<12} | {'SLA (URGENT/TOP ACTION)'}")
    print("  " + "─" * 64)
    for a in batch_result.assessments:
        top_action = a.recommended_actions[0] if a.recommended_actions else None
        sla = top_action.sla if top_action else "N/A"
        print(f"  {a.merchant_name:<18} | {a.risk_tier:<9} | {a.churn_probability:<11.1%} | {sla}")

    # Detailed action breakdown
    print(f"\n{border}")
    print("  DETAILED ACTION PLANS:")
    print(f"{border}")
    for a in batch_result.assessments:
        print(f"\n  • {a.merchant_name} [{a.risk_tier} - {a.churn_probability:.1%}]")
        print(f"    Summary   : {a.executive_summary}")
        print(f"    Incentive : {a.proposed_incentive}")
        for idx, act in enumerate(a.recommended_actions, 1):
            print(f"    {idx}. [{act.priority}] {act.action} (SLA: {act.sla} | Owner: {act.owner_role})")

    # Validated JSON export
    json_payload = batch_result.model_dump_json(indent=2)
    print(f"\n{border}")
    print("  VALIDATED JSON PAYLOAD (Batch Array):")
    print(f"{border}")
    print(json_payload)

    if output_path:
        Path(output_path).write_text(json_payload, encoding="utf-8")
        print(f"\n[INFO] Batch validated JSON saved to: {output_path}")

    print(f"\n{border}")
    print(f"  Token Usage (Batch Single-Call): Prompt = {p:,} | Completion = {c:,} | Total = {t:,}")
    print(f"{border}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Type-safe customer churn risk assessment using Structured Outputs (Pydantic)."
    )
    parser.add_argument(
        "merchant",
        nargs="?",
        default=None,
        help="Optional specific merchant to evaluate (default: evaluate ALL target accounts in batch)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Force batch evaluation for all accounts in target_customers.csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to save validated JSON payload (e.g., -o data/assessments.json)",
    )
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"[ERROR] Model artifact not found at '{MODEL_PATH}'. Run 'python src/train.py' first.", file=sys.stderr)
        sys.exit(1)

    if not TARGET_CSV.exists():
        print(f"[ERROR] Target customer dataset not found at '{TARGET_CSV}'.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(TARGET_CSV)
    model = joblib.load(MODEL_PATH)
    llm = get_llm()

    # Determine mode: Single merchant or Batch all merchants
    if args.merchant and not args.all:
        matched = df[df["customer"].str.lower() == args.merchant.strip().lower()]
        if matched.empty:
            print(f"[ERROR] Merchant '{args.merchant}' not found in target accounts.", file=sys.stderr)
            print(f"[INFO] Available target accounts: {', '.join(df['customer'].tolist())}")
            sys.exit(1)
        evaluate_single(model, matched.iloc[0].to_dict(), llm, args.output)
    else:
        # Batch mode (Default)
        evaluate_batch(model, df, llm, args.output)


if __name__ == "__main__":
    main()
