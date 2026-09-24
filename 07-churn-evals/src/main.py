import argparse
import os
import sys
from pathlib import Path

# Ensure src directory is available in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from llm import get_llm
from runner import run_benchmark

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

MODEL_PATH = ROOT / "models" / "churn_model.joblib"
DATASET_PATH = ROOT / "data" / "eval_dataset.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="07 - Churn Evals: Automated benchmark suite and LLM-as-a-Judge for customer retention."
    )
    parser.add_argument(
        "--id",
        default=None,
        help="Optional test case ID to run individually (e.g., --id TC-06)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to export the benchmark report JSON (default: data/eval_report.json)",
    )
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"[ERROR] Model artifact not found at '{MODEL_PATH}'. Run 'python src/train.py' first.", file=sys.stderr)
        sys.exit(1)

    if not DATASET_PATH.exists():
        print(f"[ERROR] Benchmark dataset not found at '{DATASET_PATH}'.", file=sys.stderr)
        sys.exit(1)

    llm = get_llm()
    # Judge can use the same configured LLM client
    judge_llm = get_llm()

    out_file = Path(args.output) if args.output else None
    run_benchmark(
        dataset_path=DATASET_PATH,
        llm=llm,
        judge_llm=judge_llm,
        filter_id=args.id,
        output_path=out_file,
    )


if __name__ == "__main__":
    main()
