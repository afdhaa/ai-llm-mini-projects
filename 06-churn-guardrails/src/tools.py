from pathlib import Path
import joblib
import pandas as pd
from langchain_core.tools import tool

ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = ROOT / "models" / "churn_model.joblib"
CUSTOMERS_CSV = ROOT / "data" / "customers.csv"
TARGET_CSV = ROOT / "data" / "target_customers.csv"
PLAYBOOK_CSV = ROOT / "data" / "retention_playbook.csv"

model = None
if MODEL_PATH.exists():
    model = joblib.load(MODEL_PATH)


def load_target_customers() -> dict:
    """Load target customer records from data/target_customers.csv."""
    if not TARGET_CSV.exists():
        return {}
    df = pd.read_csv(TARGET_CSV)
    targets = {}
    for _, row in df.iterrows():
        name = str(row.get("customer", "")).strip()
        if name:
            targets[name] = {
                "transactions": int(row.get("transactions", 0)),
                "active_days": int(row.get("active_days", 0)),
                "inactive_days": int(row.get("inactive_days", 0)),
            }
    return targets


def load_all_customers() -> dict:
    """Load historical and target customer records."""
    customers = {}
    if CUSTOMERS_CSV.exists():
        df = pd.read_csv(CUSTOMERS_CSV)
        for _, row in df.iterrows():
            name = str(row.get("customer", "")).strip()
            if name:
                customers[name] = {
                    "transactions": int(row.get("transactions", 0)),
                    "active_days": int(row.get("active_days", 0)),
                    "inactive_days": int(row.get("inactive_days", 0)),
                }
    customers.update(load_target_customers())
    return customers


def load_retention_playbooks() -> dict:
    """Load retention SOP playbooks from data/retention_playbook.csv."""
    if not PLAYBOOK_CSV.exists():
        return {}
    df = pd.read_csv(PLAYBOOK_CSV)
    playbooks = {}
    for _, row in df.iterrows():
        level = str(row.get("risk_level", "")).strip().upper()
        if not level:
            continue
        raw_actions = str(row.get("actions", ""))
        delimiter = ";" if ";" in raw_actions else "|" if "|" in raw_actions else "\n"
        playbooks[level] = {
            "sla": str(row.get("sla", "-")).strip(),
            "pic": str(row.get("pic", "-")).strip(),
            "incentive": str(row.get("incentive", "-")).strip(),
            "actions": [a.strip() for a in raw_actions.split(delimiter) if a.strip()],
        }
    return playbooks


@tool
def get_target_customers() -> str:
    """Retrieve the list of target merchant accounts from data/target_customers.csv for evaluation."""
    targets = load_target_customers()
    if not targets:
        return "No target customer records found in data/target_customers.csv."

    lines = [
        f"- {name}: {data['transactions']} transactions, {data['active_days']} active days, {data['inactive_days']} inactive days"
        for name, data in targets.items()
    ]
    return f"[Target Customer Accounts ({len(targets)} records)]:\n" + "\n".join(lines)


@tool
def list_customers() -> str:
    """List all merchant names available in the historical customer database."""
    customers = load_all_customers()
    names = list(customers.keys())
    preview = ", ".join(names[:10])
    extra = f" ...and {len(names) - 10} additional accounts." if len(names) > 10 else ""
    return f"Available accounts ({len(names)} total):\n{preview}{extra}"


@tool
def predict_churn_risk(customer_name: str) -> str:
    """Run Scikit-Learn ML inference to predict churn probability and assign a risk tier for a given customer."""
    global model
    if model is None:
        if not MODEL_PATH.exists():
            return "Error: ML model artifact not found. Please train the model first by running 'python src/train.py'."
        model = joblib.load(MODEL_PATH)

    customers = load_all_customers()
    customer = customers.get(customer_name)
    if not customer:
        # Case-insensitive lookup fallback
        matched_key = next((k for k in customers if k.lower() == customer_name.strip().lower()), None)
        if matched_key:
            customer = customers[matched_key]
            customer_name = matched_key
        else:
            return f"Error: Customer '{customer_name}' was not found. Use tool 'list_customers' to inspect valid account names."

    features = pd.DataFrame([{
        "transactions": customer["transactions"],
        "active_days": customer["active_days"],
        "inactive_days": customer["inactive_days"],
    }])

    prob = float(model.predict_proba(features)[0][1])
    if prob >= 0.70:
        risk_level = "HIGH"
    elif prob >= 0.40:
        risk_level = "MEDIUM"
    elif prob >= 0.10:
        risk_level = "LOW"
    else:
        risk_level = "NO RISK"

    return (
        f"[Scikit-Learn ML Inference Output]\n"
        f"Merchant Name: {customer_name}\n"
        f"Transactions: {customer['transactions']}\n"
        f"Active Days: {customer['active_days']}\n"
        f"Inactive Days: {customer['inactive_days']}\n"
        f"Churn Probability: {prob:.1%}\n"
        f"Risk Tier: {risk_level}"
    )


@tool
def get_retention_playbook(risk_level: str) -> str:
    """Retrieve company retention playbook SOP (SLA, owner, incentive, action steps) for a risk tier ('HIGH', 'MEDIUM', 'LOW', or 'NO RISK')."""
    level_normalized = risk_level.strip().upper()
    if level_normalized in ["SAFE", "NONE", "ZERO"]:
        level_normalized = "NO RISK"

    playbooks = load_retention_playbooks()
    playbook = playbooks.get(level_normalized)

    if not playbook:
        valid_levels = ", ".join(playbooks.keys())
        return f"Error: Invalid risk level '{risk_level}'. Supported levels: {valid_levels}."

    actions_str = "\n".join([f"  - {act}" for act in playbook["actions"]])
    return (
        f"[Retention Playbook SOP - {level_normalized}]\n"
        f"SLA Response : {playbook['sla']}\n"
        f"Account PIC  : {playbook['pic']}\n"
        f"Incentive    : {playbook['incentive']}\n"
        f"Action Plan  :\n{actions_str}"
    )
