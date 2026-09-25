import json
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from flask import Blueprint, jsonify, request
from llm_factory import get_llm_config_from_request, test_llm_connection

common_bp = Blueprint("common", __name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"


def load_ml_model():
    path = MODELS_DIR / "churn_model.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}.")
    return joblib.load(path)


def load_target_customers() -> list[dict[str, Any]]:
    path = DATA_DIR / "target_customers.csv"
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def load_accounts_financials() -> dict[str, Any]:
    path = DATA_DIR / "accounts_financials.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_support_tickets() -> list[dict[str, Any]]:
    path = DATA_DIR / "support_tickets.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_retention_playbook() -> list[dict[str, Any]]:
    path = DATA_DIR / "retention_playbook.csv"
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def get_customer_profile(customer_name: str) -> dict[str, Any]:
    """Retrieve tabular metrics, financial profile, and relevant support tickets."""
    model = load_ml_model()
    targets = load_target_customers()
    row = next((t for t in targets if t["customer"].lower() == customer_name.lower()), None)
    if not row:
        raise ValueError(f"Customer '{customer_name}' not found.")

    feats = pd.DataFrame([{
        "transactions": row["transactions"],
        "active_days": row["active_days"],
        "inactive_days": row["inactive_days"],
    }])
    churn_prob = float(model.predict_proba(feats)[0][1])

    if churn_prob < 0.20:
        risk_level = "NO RISK"
    elif churn_prob < 0.50:
        risk_level = "LOW RISK"
    elif churn_prob < 0.75:
        risk_level = "MEDIUM RISK"
    else:
        risk_level = "HIGH RISK"

    all_tickets = load_support_tickets()
    customer_tickets = [t for t in all_tickets if t.get("customer", "").lower() == customer_name.lower()]

    all_fin = load_accounts_financials()
    customer_fin = next((v for k, v in all_fin.items() if k.lower() == customer_name.lower()), {})

    return {
        "customer": row["customer"],
        "transactions": int(row["transactions"]),
        "active_days": int(row["active_days"]),
        "inactive_days": int(row["inactive_days"]),
        "churn_probability": churn_prob,
        "ml_risk_level": risk_level,
        "financials": customer_fin,
        "tickets": customer_tickets,
    }


@common_bp.route("/api/customers", methods=["GET"])
def list_customers():
    """Return all target accounts enriched with calibrated ML churn probability and financials."""
    try:
        targets = load_target_customers()
        results = [get_customer_profile(t["customer"]) for t in targets]
        return jsonify({"success": True, "customers": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@common_bp.route("/api/settings/test-connection", methods=["POST"])
def test_connection():
    """Test connection using client-provided AI configuration."""
    body = request.get_json(silent=True) or {}
    config = get_llm_config_from_request(request)
    if body:
        config.update(body)

    result = test_llm_connection(config)
    status_code = 200 if result["success"] else 400
    return jsonify(result), status_code
