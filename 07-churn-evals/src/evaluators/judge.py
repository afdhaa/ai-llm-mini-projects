import json
from schema import JudgeScore, PipelineOutput

JUDGE_PROMPT_TEMPLATE = """You are an impartial Senior AI Quality Auditor evaluating an enterprise customer retention system.

EVALUATION RUBRIC:
1. FAITHFULNESS (1-5):
   - 5: Strictly grounded in data; zero hallucinations or invented numbers.
   - 1: Hallucinates fabricated transactions or metrics.

2. SOP COMPLIANCE (1-5):
   - 5: Recommendations align closely with official playbooks (High=urgent call/discount; Medium=re-engagement/shipping; No Risk=loyalty reward).
   - 1: Violates company retention guidelines.

3. ACTIONABILITY (1-5):
   - 5: Concrete, prioritized steps with clear ownership and specific SLAs.
   - 1: Vague, useless platitudes (e.g., 'improve customer satisfaction').

DECISION RULE:
- Assign PASS if average score >= 3.5 and no score is 1.
- Assign FAIL if average score < 3.5 or any critical defect exists.

USER QUERY:
"{query}"

PIPELINE OUTPUT UNDER EVALUATION:
{output_json}

Evaluate the output objectively and populate the JudgeScore schema.
"""


def evaluate_with_judge(output: PipelineOutput, query: str, llm) -> tuple[JudgeScore, dict]:
    """Perform model-graded evaluation on pipeline output using LLM-as-a-Judge."""
    structured_judge = llm.with_structured_output(JudgeScore, include_raw=True)
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        query=query,
        output_json=output.model_dump_json(indent=2),
    )

    resp = structured_judge.invoke(prompt)
    score: JudgeScore = resp["parsed"]

    # Compute exact average
    avg = round((score.faithfulness + score.sop_compliance + score.actionability) / 3.0, 2)
    score.average_score = avg
    if avg < 3.5 or min(score.faithfulness, score.sop_compliance, score.actionability) <= 1:
        score.verdict = "FAIL"
    else:
        score.verdict = "PASS"

    tokens = {"prompt": 0, "completion": 0, "total": 0}
    raw = resp.get("raw")
    if raw and hasattr(raw, "usage_metadata") and raw.usage_metadata:
        tokens["prompt"] = raw.usage_metadata.get("input_tokens", 0) or 0
        tokens["completion"] = raw.usage_metadata.get("output_tokens", 0) or 0
        tokens["total"] = raw.usage_metadata.get("total_tokens", 0) or (tokens["prompt"] + tokens["completion"])

    return score, tokens
