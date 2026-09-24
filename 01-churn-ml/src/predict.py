import argparse
from pathlib import Path
import sys
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURE_COLS = ["transactions", "active_days", "inactive_days"]
MODEL_PATH = ROOT / "models" / "churn_model.joblib"
DEFAULT_CSV = ROOT / "data" / "target_customers.csv"


def print_formula_summary(model) -> None:
    """Print formula summary for the Logistic Regression pipeline."""
    clf = model.named_steps.get("classifier")
    if clf is None:
        return
    weights = ", ".join(f"{name}: {coef:+.3f}" for name, coef in zip(FEATURE_COLS, clf.coef_[0]))
    print("\n" + "─" * 60)
    print("  MODEL FORMULA (StandardScaler -> LogisticRegression)")
    print(f"  • logit = {clf.intercept_[0]:+.4f} + sum(coef_i * z_i)")
    print(f"    Feature weights (z) -> [{weights}]")
    print("  • churn_probability = 1 / (1 + exp(-logit))")
    print("─" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict customer churn probability using Logistic Regression.")
    parser.add_argument("csv_path", nargs="?", default=None, help="Path to input CSV (default: data/target_customers.csv)")
    parser.add_argument("-o", "--output", default=None, help="Path to save prediction output CSV")
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"[ERROR] Model artifact not found at '{MODEL_PATH}'. Run 'python src/train.py' first.", file=sys.stderr)
        sys.exit(1)

    csv_path = Path(args.csv_path).resolve() if args.csv_path else DEFAULT_CSV
    if not csv_path.exists():
        print(f"[ERROR] Input CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)
    if "customer" not in df.columns:
        df["customer"] = [f"Customer #{i+1}" for i in range(len(df))]

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba(df[FEATURE_COLS])[:, 1]
    df["churn_probability"] = probabilities
    df["churn_percentage"] = [f"{p * 100:.1f}%" for p in probabilities]

    print(f"\n[INFO] Churn Prediction Results ({csv_path.name}):")
    cols = ["customer"] + FEATURE_COLS + ["churn_percentage"]
    print(df[cols].to_string(index=False))

    print_formula_summary(model)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"[INFO] Results saved to: {args.output}")


if __name__ == "__main__":
    main()
