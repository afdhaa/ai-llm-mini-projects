from pathlib import Path
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "customers.csv")

X = df[["transactions", "active_days", "inactive_days"]]
y = (df["status"] == "churned").astype(int)

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(random_state=42))
])

model.fit(X, y)

(ROOT / "models").mkdir(exist_ok=True)
joblib.dump(model, ROOT / "models" / "churn_model.joblib")

print("Model trained: models/churn_model.joblib")
