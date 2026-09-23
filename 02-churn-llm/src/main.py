import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from dotenv import load_dotenv

from llm import generate_explanation

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CUSTOMERS_CSV = ROOT / "data" / "customers.csv"
if not CUSTOMERS_CSV.exists():
    print(f"[ERROR] Customer data not found at '{CUSTOMERS_CSV}'.", file=sys.stderr)
    sys.exit(1)

df = pd.read_csv(CUSTOMERS_CSV)
target_name = sys.argv[1] if len(sys.argv) > 1 else "Store B"
matched = df[df["customer"].str.lower() == target_name.lower()]
customer = (matched if not matched.empty else df).iloc[0].to_dict()

context = f"""
Merchant Name: {customer["customer"]}
Total Transactions: {customer["transactions"]}
Active Days: {customer["active_days"]}
Inactive Days: {customer["inactive_days"]}
"""

prompt = f"""
You are a Customer Success Operations Analyst. Evaluate the churn risk of the following merchant using only their activity metrics.

Account Activity Data:
{context}

Requirements:
- Style: Direct, analytical bullet points (-) for CLI review. Do not use bold markdown (**) or headers (###).
- Structure:
  1. Assessed Risk Tier: Assign one tier (HIGH, MEDIUM, or LOW) with estimated churn likelihood.
  2. Behavioral Diagnosis: Explain primary usage trends and disengagement drivers.
  3. Action Plan: Provide 2 immediate, high-impact operational intervention steps.
"""

provider_name = os.getenv("AI_PROVIDER", "gemini")
explanation, usage = generate_explanation(prompt)

border = "=" * 60
print(f"\n{border}")
print(f"  PURE LLM CHURN ASSESSMENT: {customer['customer']} [{provider_name.upper()}]")
print(f"{border}")
print(f"  Total Transactions : {customer['transactions']}")
print(f"  Active Days        : {customer['active_days']}")
print(f"  Inactive Days      : {customer['inactive_days']}")
print(f"  Evaluation Mode    : Zero-Shot Prompting (No ML Pipeline)")
print(f"{border}\n")
print(explanation)
print(f"\n{border}")
print(f"  Token Usage: Prompt = {usage.prompt_tokens:,} | Completion = {usage.completion_tokens:,} | Total = {usage.total_tokens:,}")
print(f"{border}\n")
