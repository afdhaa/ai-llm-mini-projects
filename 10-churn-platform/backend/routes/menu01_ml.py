import time
from pathlib import Path
from flask import Blueprint, jsonify, request
import pandas as pd
from routes.common import load_ml_model, DATA_DIR

menu01_bp = Blueprint("menu01", __name__)


@menu01_bp.route("/api/tier01/predict", methods=["POST"])
def predict_churn():
    t0 = time.time()
    try:
        data = request.get_json() or {}
        tx = float(data.get("transactions", 100))
        act = float(data.get("active_days", 10))
        inact = float(data.get("inactive_days", 15))

        model = load_ml_model()
        feats = pd.DataFrame([{
            "transactions": tx,
            "active_days": act,
            "inactive_days": inact,
        }])
        prob = float(model.predict_proba(feats)[0][1])

        if prob < 0.20:
            risk = "NO RISK"
            color = "green"
        elif prob < 0.50:
            risk = "LOW RISK"
            color = "blue"
        elif prob < 0.75:
            risk = "MEDIUM RISK"
            color = "yellow"
        else:
            risk = "HIGH RISK"
            color = "red"

        latency_ms = round((time.time() - t0) * 1000, 2)

        return jsonify({
            "success": True,
            "transactions": int(tx),
            "active_days": int(act),
            "inactive_days": int(inact),
            "churn_probability": prob,
            "churn_percentage": f"{prob:.1%}",
            "risk_level": risk,
            "color": color,
            "latency_ms": latency_ms,
            "model_type": "LogisticRegression (StandardScaler)",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@menu01_bp.route("/api/tier01/batch", methods=["GET", "POST"])
def predict_batch_churn():
    """Compute calibrated churn predictions for all target customer accounts simultaneously."""
    t0 = time.time()
    try:
        from routes.common import load_target_customers
        targets = load_target_customers()
        model = load_ml_model()

        results = []
        for t in targets:
            feats = pd.DataFrame([{
                "transactions": float(t["transactions"]),
                "active_days": float(t["active_days"]),
                "inactive_days": float(t["inactive_days"]),
            }])
            prob = float(model.predict_proba(feats)[0][1])
            if prob < 0.20:
                risk = "NO RISK"
            elif prob < 0.50:
                risk = "LOW RISK"
            elif prob < 0.75:
                risk = "MEDIUM RISK"
            else:
                risk = "HIGH RISK"

            results.append({
                "customer": t["customer"],
                "transactions": int(t["transactions"]),
                "active_days": int(t["active_days"]),
                "inactive_days": int(t["inactive_days"]),
                "churn_probability": prob,
                "churn_percentage": f"{prob:.1%}",
                "risk_level": risk,
            })

        results.sort(key=lambda x: x["churn_probability"], reverse=True)
        latency_ms = round((time.time() - t0) * 1000, 2)

        return jsonify({
            "success": True,
            "total_accounts": len(results),
            "results": results,
            "latency_ms": latency_ms,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@menu01_bp.route("/api/tier01/dataset", methods=["GET"])
def get_training_dataset():
    try:
        df = pd.read_csv(DATA_DIR / "customers.csv")
        return jsonify({
            "success": True,
            "total_records": len(df),
            "records": df.head(100).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
