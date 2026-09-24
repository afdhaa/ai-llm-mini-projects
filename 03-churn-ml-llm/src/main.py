import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import pandas as pd
from dotenv import load_dotenv

from llm import generate_explanation

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MODEL_PATH = ROOT / "models" / "churn_model.joblib"
if not MODEL_PATH.exists():
    print(f"[ERROR] Model artifact not found at '{MODEL_PATH}'. Run 'python src/train.py' first.", file=sys.stderr)
    sys.exit(1)

model = joblib.load(MODEL_PATH)

# Load customer record from target dataset (CLI argument or default: Store Critical)
target_csv = ROOT / "data" / "target_customers.csv"
if not target_csv.exists():
    print(f"[ERROR] Target customer data not found at '{target_csv}'.", file=sys.stderr)
    sys.exit(1)
df = pd.read_csv(target_csv)
target_name = sys.argv[1] if len(sys.argv) > 1 else "Store Critical"
matched = df[df["customer"].str.lower() == target_name.lower()]
customer = (matched if not matched.empty else df).iloc[0].to_dict()

features = ["transactions", "active_days", "inactive_days"]
input_df = pd.DataFrame([customer])[features]
probability = float(model.predict_proba(input_df)[0][1])

risk_level = "HIGH" if probability >= 0.7 else "MEDIUM" if probability >= 0.4 else "LOW"

context = f"""
Merchant Name: {customer["customer"]}
Total Transactions: {customer["transactions"]}
Active Days: {customer["active_days"]}
Inactive Days: {customer["inactive_days"]}
ML Churn Probability: {probability:.1%}
Assessed Risk Tier: {risk_level}
"""

prompt = f"""
Analyze the following merchant churn risk profile for an operational Customer Success review:
- Style: Direct, professional, concise bullet points (-) for CLI display. Do not use bold markdown (**) or headers (###).
- Structure:
  1. Risk Status (the ML probability is an early warning indicator, not an absolute certainty).
  2. Primary Drivers (usage trajectory, activity vs. dormancy ratios).
  3. Action Plan (2 concrete operational steps for the account representative).

Account Data:
{context}
"""

provider_name = os.getenv("AI_PROVIDER", "gemini")
explanation, usage = generate_explanation(prompt)

border = "=" * 60
print(f"\n{border}")
print(f"  CHURN RISK BRIEFING: {customer['customer']} [{provider_name.upper()}]")
print(f"{border}")
print(f"  Total Transactions : {customer['transactions']}")
print(f"  Active Days        : {customer['active_days']}")
print(f"  Inactive Days      : {customer['inactive_days']}")
print(f"  ML Predicted Risk  : {probability:.1%} [{risk_level}]")
print(f"{border}\n")
print(explanation)
print(f"\n{border}")
print(f"  Token Usage: Prompt = {usage.prompt_tokens:,} | Completion = {usage.completion_tokens:,} | Total = {usage.total_tokens:,}")
print(f"{border}\n")
