# 01 - Churn ML

Baseline tabular machine learning pipeline for customer churn prediction using Scikit-Learn.

## Dataset Structure

- **Training Data (`data/customers.csv`)**: Historical records with `status` label (`active` / `churned`).
- **Target / Inference Data (`data/target_customers.csv`)**: Merchant records to evaluate without target labels.

## Pipeline Architecture

```text
data/customers.csv (Training Data)
        │
        ▼
   src/train.py (StandardScaler + Logistic Regression)
        │
        ▼
models/churn_model.joblib
        │
        ▼
   src/predict.py  <──  data/target_customers.csv (Inference Data)
        │
        ▼
Prediction Output Table & Linear Equation Summary
```

## Setup & Execution

```bash
# 1. Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Train model
python src/train.py

# 3. Run prediction (default: data/target_customers.csv)
python src/main.py
# or:
python src/predict.py

# Run prediction on custom CSV:
python src/predict.py path/to/customers.csv

# Save prediction results to output CSV:
python src/predict.py -o data/predictions.csv
```

No external API keys or services required.
