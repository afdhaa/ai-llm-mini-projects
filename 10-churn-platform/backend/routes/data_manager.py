import json
import shutil
import time
from pathlib import Path
from typing import Any
import joblib
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

data_mgr_bp = Blueprint("data_mgr", __name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
BACKUP_DIR = DATA_DIR / "backup"


# --- Helpers ---

def get_target_df() -> pd.DataFrame:
    path = DATA_DIR / "target_customers.csv"
    if not path.exists():
        return pd.DataFrame(columns=["customer", "transactions", "active_days", "inactive_days"])
    return pd.read_csv(path)


def save_target_df(df: pd.DataFrame) -> None:
    path = DATA_DIR / "target_customers.csv"
    df.to_csv(path, index=False)


def get_financials_dict() -> dict[str, Any]:
    path = DATA_DIR / "accounts_financials.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_financials_dict(data: dict[str, Any]) -> None:
    path = DATA_DIR / "accounts_financials.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_tickets_list() -> list[dict[str, Any]]:
    path = DATA_DIR / "support_tickets.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tickets_list(tickets: list[dict[str, Any]]) -> None:
    path = DATA_DIR / "support_tickets.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)


def get_training_df() -> pd.DataFrame:
    path = DATA_DIR / "customers.csv"
    return pd.read_csv(path)


def save_training_df(df: pd.DataFrame) -> None:
    path = DATA_DIR / "customers.csv"
    df.to_csv(path, index=False)


# --- Target Customers Endpoints ---

@data_mgr_bp.route("/api/targets", methods=["GET"])
def list_targets():
    """List all target accounts along with metrics, financials, and tickets."""
    try:
        targets_df = get_target_df()
        financials = get_financials_dict()
        tickets = get_tickets_list()

        results = []
        for _, row in targets_df.iterrows():
            name = str(row["customer"])
            fin = financials.get(name) or {}
            cust_tickets = [t for t in tickets if t.get("customer", "").lower() == name.lower()]

            results.append({
                "customer": name,
                "transactions": int(row["transactions"]),
                "active_days": int(row["active_days"]),
                "inactive_days": int(row["inactive_days"]),
                "financials": fin,
                "tickets": cust_tickets,
            })
        return jsonify({"success": True, "targets": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@data_mgr_bp.route("/api/targets", methods=["POST"])
def upsert_target():
    """Create or update a target account with activity metrics, financials, and support tickets."""
    try:
        data = request.get_json() or {}
        name = str(data.get("customer", "")).strip()
        if not name:
            return jsonify({"success": False, "error": "Customer name is required"}), 400

        tx = int(data.get("transactions", 100))
        act = int(data.get("active_days", 10))
        inact = int(data.get("inactive_days", 15))

        # 1. Update target_customers.csv
        df = get_target_df()
        idx = df[df["customer"].str.lower() == name.lower()].index
        if len(idx) > 0:
            df.loc[idx[0], "transactions"] = tx
            df.loc[idx[0], "active_days"] = act
            df.loc[idx[0], "inactive_days"] = inact
        else:
            new_row = pd.DataFrame([{
                "customer": name,
                "transactions": tx,
                "active_days": act,
                "inactive_days": inact,
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        save_target_df(df)

        # 2. Update financials
        fin = get_financials_dict()
        cust_fin = data.get("financials") or {}
        fin[name] = {
            "customer": name,
            "customer_tier": cust_fin.get("customer_tier", "GROWTH"),
            "monthly_gmv_idr": float(cust_fin.get("monthly_gmv_idr", 50000000)),
            "platform_fee_rate": float(cust_fin.get("platform_fee_rate", 0.02)),
            "monthly_revenue_idr": float(cust_fin.get("monthly_revenue_idr", 1000000)),
            "pending_payout_idr": float(cust_fin.get("pending_payout_idr", 0)),
            "max_retention_budget_idr": float(cust_fin.get("max_retention_budget_idr", 2000000)),
            "contract_renewal_days": int(cust_fin.get("contract_renewal_days", 30)),
            "margin_percentage": float(cust_fin.get("margin_percentage", 0.65)),
        }
        save_financials_dict(fin)

        # 3. Update tickets if provided
        incoming_tickets = data.get("tickets")
        if incoming_tickets is not None:
            all_tickets = get_tickets_list()
            # remove existing tickets for this customer
            all_tickets = [t for t in all_tickets if t.get("customer", "").lower() != name.lower()]
            for t in incoming_tickets:
                t["customer"] = name
                all_tickets.append(t)
            save_tickets_list(all_tickets)

        return jsonify({
            "success": True,
            "message": f"Target account '{name}' saved successfully.",
            "target": {
                "customer": name,
                "transactions": tx,
                "active_days": act,
                "inactive_days": inact,
                "financials": fin[name],
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@data_mgr_bp.route("/api/targets/<customer_name>", methods=["DELETE"])
def delete_target(customer_name: str):
    """Delete a target account from CSV, financials, and tickets."""
    try:
        df = get_target_df()
        df = df[df["customer"].str.lower() != customer_name.lower()]
        save_target_df(df)

        fin = get_financials_dict()
        key_to_del = next((k for k in fin.keys() if k.lower() == customer_name.lower()), None)
        if key_to_del:
            del fin[key_to_del]
            save_financials_dict(fin)

        tickets = get_tickets_list()
        tickets = [t for t in tickets if t.get("customer", "").lower() != customer_name.lower()]
        save_tickets_list(tickets)

        return jsonify({"success": True, "message": f"Target '{customer_name}' removed."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# --- Training Dataset Endpoints ---

@data_mgr_bp.route("/api/training", methods=["GET"])
def list_training_data():
    """List all rows in training dataset customers.csv."""
    try:
        df = get_training_df()
        return jsonify({
            "success": True,
            "total_records": len(df),
            "churn_count": int((df["status"] == "churned").sum()),
            "active_count": int((df["status"] == "active").sum()),
            "records": df.to_dict(orient="records"),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@data_mgr_bp.route("/api/training", methods=["POST"])
def add_training_row():
    """Add or update a row in customers.csv."""
    try:
        data = request.get_json() or {}
        name = str(data.get("customer", "")).strip()
        tx = int(data.get("transactions", 100))
        act = int(data.get("active_days", 10))
        inact = int(data.get("inactive_days", 15))
        status = str(data.get("status", "active")).strip().lower()

        if status not in ("active", "churned"):
            status = "active"

        df = get_training_df()
        idx = df[df["customer"].str.lower() == name.lower()].index
        if len(idx) > 0:
            df.loc[idx[0], "transactions"] = tx
            df.loc[idx[0], "active_days"] = act
            df.loc[idx[0], "inactive_days"] = inact
            df.loc[idx[0], "status"] = status
        else:
            new_row = pd.DataFrame([{
                "customer": name,
                "transactions": tx,
                "active_days": act,
                "inactive_days": inact,
                "status": status,
            }])
            df = pd.concat([df, new_row], ignore_index=True)

        save_training_df(df)
        return jsonify({
            "success": True,
            "message": f"Training record '{name}' saved ({status}).",
            "total_records": len(df),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@data_mgr_bp.route("/api/training/<customer_name>", methods=["DELETE"])
def delete_training_row(customer_name: str):
    """Delete a row from customers.csv."""
    try:
        df = get_training_df()
        df = df[df["customer"].str.lower() != customer_name.lower()]
        save_training_df(df)
        return jsonify({"success": True, "message": f"Training row '{customer_name}' deleted.", "total_records": len(df)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@data_mgr_bp.route("/api/training/retrain", methods=["POST"])
def retrain_model():
    """Retrain Scikit-Learn Logistic Regression model on current customers.csv and save to models/churn_model.joblib."""
    t0 = time.time()
    try:
        df = get_training_df()
        X = df[["transactions", "active_days", "inactive_days"]]
        y = (df["status"] == "churned").astype(int)

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42))
        ])

        pipeline.fit(X, y)
        accuracy = float(pipeline.score(X, y))

        model_path = MODELS_DIR / "churn_model.joblib"
        joblib.dump(pipeline, model_path)
        latency_ms = int((time.time() - t0) * 1000)

        # Extract coefficients
        scaler = pipeline.named_steps["scaler"]
        clf = pipeline.named_steps["classifier"]
        coeffs = {
            "transactions": round(float(clf.coef_[0][0]), 4),
            "active_days": round(float(clf.coef_[0][1]), 4),
            "inactive_days": round(float(clf.coef_[0][2]), 4),
            "intercept": round(float(clf.intercept_[0]), 4),
        }

        return jsonify({
            "success": True,
            "message": "Scikit-Learn model successfully retrained and deployed.",
            "accuracy": round(accuracy * 100, 2),
            "accuracy_formatted": f"{accuracy:.1%}",
            "total_samples": len(df),
            "churned_samples": int(y.sum()),
            "active_samples": int((y == 0).sum()),
            "coefficients": coeffs,
            "latency_ms": latency_ms,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@data_mgr_bp.route("/api/data/reset", methods=["POST"])
def reset_to_defaults():
    """Reset all datasets from backup copy."""
    try:
        if not BACKUP_DIR.exists():
            return jsonify({"success": False, "error": "Backup directory not found."}), 404

        for f in BACKUP_DIR.glob("*.*"):
            shutil.copy2(f, DATA_DIR / f.name)

        # Retrain model on default dataset
        df = get_training_df()
        X = df[["transactions", "active_days", "inactive_days"]]
        y = (df["status"] == "churned").astype(int)
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42))
        ])
        pipeline.fit(X, y)
        joblib.dump(pipeline, MODELS_DIR / "churn_model.joblib")

        return jsonify({
            "success": True,
            "message": "All datasets and models reset to factory defaults.",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
