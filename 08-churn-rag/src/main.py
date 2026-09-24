import argparse
import json
import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from dotenv import load_dotenv

from llm import get_llm
from pipeline import ChurnRagPipeline
from schema import ChurnRagReport

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TARGET_CSV = ROOT / "data" / "target_customers.csv"


def print_report(report: ChurnRagReport) -> None:
    """Print an executive, formatted terminal scorecard contrasting ML, SOP, and RAG."""
    border = "=" * 76
    sub_border = "-" * 76

    print(f"\n{border}")
    print(f"  CHURN INTELLIGENCE REPORT: {report.customer.upper()}")
    print(f"{border}")

    # 1. Tabular ML Prediction
    print("  [1] TABULAR MACHINE LEARNING INFERENCE (Scikit-Learn)")
    print(f"      • Calibrated Churn Probability : {report.churn_probability:.1%}")
    print(f"      • Statistical Risk Tier        : [{report.ml_risk_level}]")
    print(
        f"      • Activity Metrics             : {report.transactions} txs | "
        f"{report.active_days} active days | {report.inactive_days} inactive days"
    )

    # 2. Standard Playbook SOP
    print(f"\n{sub_border}")
    print("  [2] STANDARD SOP PLAYBOOK (Generic Guidance - No Unstructured Context)")
    print(f"      • Standard SLA                 : {report.sop_baseline.sla}")
    print(f"      • Default PIC                  : {report.sop_baseline.pic}")
    print(f"      • Default Incentive / Offer    : {report.sop_baseline.generic_incentive}")
    print("      • Prescribed Generic Actions   :")
    for act in report.sop_baseline.generic_actions:
        print(f"        - {act}")

    # 3. RAG Support Tickets Evidence
    print(f"\n{sub_border}")
    print(f"  [3] RAG RETRIEVAL: UNSTRUCTURED TICKETS ({len(report.retrieved_tickets)} records found)")
    if report.retrieved_tickets:
        for idx, t in enumerate(report.retrieved_tickets, 1):
            print(f"      {idx}. [{t.ticket_id}] [{t.channel}] [{t.sentiment}] {t.timestamp}")
            print(f"         {t.snippet}")
            if t.sentiment_reason:
                print(f"         ↳ Sentiment Rationale: {t.sentiment_reason}")
    else:
        print("      • (No historical support tickets or complaints found on file)")
    # 4. Context-Aware Synthesis
    intervention = report.tailored_intervention
    print(f"\n{sub_border}")
    print("  [4] CONTEXT-AWARE RETENTION INTERVENTION (Hybrid ML + RAG Synthesis)")
    print(f"      • Primary Root Cause           : {intervention.primary_root_cause.value}")
    print(f"      • Operational Urgency          : [{intervention.urgency}]")
    print(f"      • Is Standard SOP Adequate?    : {'YES' if intervention.is_sop_adequate else 'NO (OVERRIDE REQUIRED)'}")
    print(f"      • Root Cause Narrative         : {intervention.root_cause_explanation}")
    print(f"      • Override Justification       : {intervention.override_justification}")
    print(f"      • Recommended Owner / PIC      : {intervention.recommended_pic}")
    print("      • Tailored Action Plan         :")
    for idx, act in enumerate(intervention.tailored_action_items, 1):
        print(f"        {idx}. {act}")
    if report.token_usage and report.token_usage.total_tokens > 0:
        print(f"{border}")
        print(
            f"  Token Usage: Prompt = {report.token_usage.prompt_tokens:,} | "
            f"Completion = {report.token_usage.completion_tokens:,} | "
            f"Total = {report.token_usage.total_tokens:,}"
        )
    print(f"{border}\n")


def main():
    parser = argparse.ArgumentParser(
        description="08-churn-rag: Hybrid Tabular ML + Unstructured Customer Tickets (RAG) Retention Pipeline"
    )
    parser.add_argument(
        "--id",
        "-i",
        default="Store Critical",
        help="Target customer name from target_customers.csv or 'all' to evaluate full batch (default: 'Store Critical')",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional path to export validated JSON assessment report.",
    )
    parser.add_argument(
        "--query",
        "-q",
        default="churn risk complaint technical issue pricing cancellation",
        help="Semantic focus query for RAG ticket ranking.",
    )

    args = parser.parse_args()

    # Initialize LLM if credentials exist, else fallback gracefully
    llm = None
    try:
        llm = get_llm()
    except Exception as e:
        print(f"[INFO] Running in offline heuristic mode ({e})")

    pipeline = ChurnRagPipeline(llm=llm)

    if not TARGET_CSV.exists():
        print(f"[ERROR] Target dataset not found at {TARGET_CSV}")
        sys.exit(1)

    df_target = pd.read_csv(TARGET_CSV)

    if args.id.lower() == "all":
        reports = []
        total_p, total_c, total_t = 0, 0, 0
        for _, row in df_target.iterrows():
            customer_data = row.to_dict()
            report = pipeline.synthesize(customer_data, focus_query=args.query)
            print_report(report)
            reports.append(report.model_dump())
            if report.token_usage:
                total_p += report.token_usage.prompt_tokens
                total_c += report.token_usage.completion_tokens
                total_t += report.token_usage.total_tokens

        if total_t > 0:
            border = "=" * 76
            print(f"\n{border}")
            print("  BATCH CUMULATIVE TOKEN ECONOMICS (Across all merchant evaluations):")
            print(f"  Prompt = {total_p:,} | Completion = {total_c:,} | Total = {total_t:,}")
            print(f"{border}\n")

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(reports, indent=2), encoding="utf-8")
            print(f"[SUCCESS] Exported {len(reports)} batch reports to: {args.output}")
    else:
        matched = df_target[df_target["customer"].str.lower() == args.id.lower()]
        if matched.empty:
            print(f"[ERROR] Customer '{args.id}' not found in {TARGET_CSV}")
            print(f"Available customers: {df_target['customer'].tolist()}")
            sys.exit(1)

        customer_data = matched.iloc[0].to_dict()
        report = pipeline.synthesize(customer_data, focus_query=args.query)
        print_report(report)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
            print(f"[SUCCESS] Exported validated report to: {args.output}")


if __name__ == "__main__":
    main()
