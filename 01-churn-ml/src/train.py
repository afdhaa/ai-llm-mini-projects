import argparse
from pathlib import Path
import sys
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURE_COLS = ["transactions", "active_days", "inactive_days"]
TARGET_COL = "status"
DEFAULT_TRAIN_PATH = ROOT / "data" / "customers.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Logistic Regression model for customer churn prediction.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=None,
        help="Path to training CSV file (optional, default: data/customers.csv)",
    )
    args = parser.parse_args()

    train_path = Path(args.csv_path).resolve() if args.csv_path else DEFAULT_TRAIN_PATH

    if not train_path.exists():
        print(f"[ERROR] Training data not found at '{train_path}'", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Loading training dataset: {train_path}")
    df = pd.read_csv(train_path)

    missing_cols = [col for col in FEATURE_COLS + [TARGET_COL] if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns in dataset: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    X = df[FEATURE_COLS]
    y = (df[TARGET_COL] == "churned").astype(int)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(random_state=42))
    ])

    model.fit(X, y)

    models_dir = ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    model_output = models_dir / "churn_model.joblib"
    joblib.dump(model, model_output)

    print(f"[SUCCESS] Model trained successfully ({len(df)} samples)")
    print(f"[SUCCESS] Saved artifact to: {model_output}")


if __name__ == "__main__":
    main()
