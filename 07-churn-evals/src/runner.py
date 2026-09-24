from datetime import datetime
import json
import os
from pathlib import Path
import time

from evaluators import evaluate_rules, evaluate_with_judge
from pipeline import run_pipeline
from schema import BenchmarkSummary, TestCaseResult


def run_benchmark(
    dataset_path: Path,
    llm,
    judge_llm,
    filter_id: str | None = None,
    output_path: Path | None = None,
) -> BenchmarkSummary:
    """Run automated benchmark suite across all or filtered test cases."""
    raw_data = json.loads(dataset_path.read_text(encoding="utf-8"))
    test_cases = [tc for tc in raw_data if not filter_id or tc["id"].lower() == filter_id.lower()]

    if not test_cases:
        raise ValueError(f"No test cases matching filter '{filter_id}'.")

    provider_name = os.getenv("AI_PROVIDER", "gemini").upper()
    model_name = os.getenv("AI_MODEL", "default")
    border = "=" * 70

    print(f"\n{border}")
    print(f"  AUTOMATED CHURN AI BENCHMARK SUITE [{provider_name} - {model_name}]")
    print(f"{border}")
    print(f"  Total Test Cases to Evaluate: {len(test_cases)}")
    print(f"  Pillars: Deterministic Rule Assertions + LLM-as-a-Judge Rubrics\n")

    results: list[TestCaseResult] = []
    total_tokens_all = 0
    total_latency_all = 0.0

    for idx, tc in enumerate(test_cases, 1):
        tc_id = tc["id"]
        desc = tc["description"]
        query = tc["query"]
        category = tc.get("category", "STANDARD")

        print(f"  [{idx}/{len(test_cases)}] Running {tc_id} ({category}): \"{desc}\"...")

        # 1. Execute SUT Pipeline
        output, p_tokens, latency = run_pipeline(query, llm)
        total_latency_all += latency
        case_tokens = {
            "pipeline_prompt": p_tokens["prompt"],
            "pipeline_completion": p_tokens["completion"],
            "pipeline_total": p_tokens["total"],
            "judge_total": 0,
            "total": p_tokens["total"],
        }

        # 2. Evaluate Deterministic Rules
        assertions = evaluate_rules(output, tc)
        rules_passed = sum(1 for a in assertions if a.passed)
        rules_total = len(assertions)
        rules_ok = (rules_passed == rules_total)

        # 3. Model-Graded Evaluation (LLM-as-a-Judge)
        judge_score = None
        judge_verdict_ok = True
        if tc.get("expected_domain", True) and output.is_valid_domain and output.evaluations:
            judge_score, j_tokens = evaluate_with_judge(output, query, judge_llm)
            case_tokens["judge_total"] = j_tokens["total"]
            case_tokens["total"] += j_tokens["total"]
            judge_verdict_ok = (judge_score.verdict == "PASS")

        total_tokens_all += case_tokens["total"]

        # 4. Synthesize Overall Case Verdict
        overall_pass = rules_ok and judge_verdict_ok
        verdict_str = "PASS" if overall_pass else "FAIL"

        result_item = TestCaseResult(
            test_id=tc_id,
            category=category,
            description=desc,
            query=query,
            latency_seconds=latency,
            token_usage=case_tokens,
            rules_passed=rules_passed,
            rules_total=rules_total,
            rule_assertions=assertions,
            judge_score=judge_score,
            overall_verdict=verdict_str,
        )
        results.append(result_item)

        # Print inline result line
        judge_display = f"Judge: {judge_score.average_score:.1f}/5.0" if judge_score else "Judge: N/A"
        print(f"       -> Result: {verdict_str} | Rules: {rules_passed}/{rules_total} | {judge_display} | Time: {latency}s")

    # ==============================================================================
    # AGGREGATE SUMMARY METRICS
    # ==============================================================================
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.overall_verdict == "PASS")
    failed_cases = total_cases - passed_cases
    pass_rate = round((passed_cases / total_cases) * 100.0, 1)

    total_rules = sum(r.rules_total for r in results)
    passed_rules = sum(r.rules_passed for r in results)
    rule_pass_rate = round((passed_rules / total_rules) * 100.0, 1) if total_rules > 0 else 100.0

    scored_cases = [r.judge_score for r in results if r.judge_score is not None]
    if scored_cases:
        avg_faith = round(sum(s.faithfulness for s in scored_cases) / len(scored_cases), 2)
        avg_sop = round(sum(s.sop_compliance for s in scored_cases) / len(scored_cases), 2)
        avg_act = round(sum(s.actionability for s in scored_cases) / len(scored_cases), 2)
        avg_judge = round(sum(s.average_score for s in scored_cases) / len(scored_cases), 2)
    else:
        avg_faith, avg_sop, avg_act, avg_judge = 5.0, 5.0, 5.0, 5.0

    avg_latency = round(total_latency_all / total_cases, 2)

    summary = BenchmarkSummary(
        timestamp=datetime.now().isoformat(),
        provider=provider_name,
        model=model_name,
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        pass_rate_percent=pass_rate,
        rule_pass_rate_percent=rule_pass_rate,
        average_faithfulness=avg_faith,
        average_sop_compliance=avg_sop,
        average_actionability=avg_act,
        average_judge_score=avg_judge,
        total_tokens=total_tokens_all,
        average_latency_seconds=avg_latency,
        results=results,
    )

    # ==============================================================================
    # TERMINAL BENCHMARK SCORECARD
    # ==============================================================================
    print(f"\n{border}")
    print("  TEST CASE EXECUTION MATRIX")
    print(f"{border}")
    print(f"  {'ID':<7} | {'CATEGORY':<21} | {'RULES':<7} | {'JUDGE':<9} | {'TIME':<6} | {'VERDICT'}")
    print("  " + "─" * 66)
    for r in results:
        j_str = f"{r.judge_score.average_score:.1f}/5.0" if r.judge_score else "N/A"
        print(f"  {r.test_id:<7} | {r.category:<21} | {r.rules_passed}/{r.rules_total:<5} | {j_str:<9} | {r.latency_seconds:<5}s | {r.overall_verdict}")

    print(f"\n{border}")
    print("  AGGREGATED BENCHMARK SCORECARD")
    print(f"{border}")
    print(f"  Overall Pass Rate        : {pass_rate}% ({passed_cases}/{total_cases} passed)")
    print(f"  Deterministic Rule Pass  : {rule_pass_rate}% ({passed_rules}/{total_rules} assertions)")
    print(f"  Average Faithfulness     : {avg_faith} / 5.0 (Hallucination metric)")
    print(f"  Average SOP Compliance   : {avg_sop} / 5.0 (Policy adherence)")
    print(f"  Average Actionability    : {avg_act} / 5.0 (Operational clarity)")
    print(f"  Overall Judge Score      : {avg_judge} / 5.0")
    print(f"  Average Latency          : {avg_latency}s per test case")
    print(f"  Total Token Consumption  : {total_tokens_all:,} tokens")
    print(f"{border}\n")

    # Export report JSON
    target_out = output_path or (dataset_path.parent / "eval_report.json")
    target_out.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    print(f"[SUCCESS] Complete benchmark audit report exported to: {target_out}\n")

    return summary
