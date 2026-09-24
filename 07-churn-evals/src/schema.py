from typing import Literal, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# 1. SYSTEM UNDER TEST (SUT) SCHEMAS
# ==============================================================================
class ActionItem(BaseModel):
    action: str
    priority: Literal["URGENT", "HIGH", "MEDIUM", "LOW"]
    sla: str
    owner_role: str


class AccountEvaluation(BaseModel):
    merchant_name: str
    risk_tier: Literal["HIGH", "MEDIUM", "LOW", "NO RISK"]
    churn_probability: float = Field(ge=0.0, le=1.0)
    primary_drivers: list[str]
    recommended_actions: list[ActionItem]
    proposed_incentive: str
    executive_summary: str


class PipelineOutput(BaseModel):
    is_valid_domain: bool
    guardrail_status: Literal["PASSED", "SANITIZED", "BLOCKED"]
    guardrail_notice: Optional[str] = None
    sanitized_query: str
    evaluations: list[AccountEvaluation] = Field(default_factory=list)
    rejection_reason: Optional[str] = None


# ==============================================================================
# 2. EVALUATION & BENCHMARK SCHEMAS
# ==============================================================================
class RuleAssertion(BaseModel):
    """Result of a deterministic rule-based assertion."""

    name: str = Field(..., description="Name of the assertion check.")
    passed: bool = Field(..., description="True if assertion met; False otherwise.")
    message: str = Field(..., description="Diagnostic detail or failure description.")


class JudgeScore(BaseModel):
    """Model-graded evaluation from LLM-as-a-Judge."""

    faithfulness: int = Field(
        ...,
        ge=1,
        le=5,
        description="Factual consistency (1-5): No hallucinations or unfounded metrics.",
    )
    sop_compliance: int = Field(
        ...,
        ge=1,
        le=5,
        description="Policy adherence (1-5): Proper SLA, role, and actions matching SOP.",
    )
    actionability: int = Field(
        ...,
        ge=1,
        le=5,
        description="Operational clarity (1-5): Clear, concrete, practical steps.",
    )
    average_score: float = Field(
        ...,
        description="Average score across the 3 rubric criteria.",
    )
    verdict: Literal["PASS", "FAIL"] = Field(
        ...,
        description="PASS if average_score >= 3.5 and no critical flaw; otherwise FAIL.",
    )
    critique: str = Field(
        ...,
        description="Qualitative justification and critique from the judge.",
    )


class TestCaseResult(BaseModel):
    """Aggregated evaluation result for a single benchmark test case."""

    test_id: str
    category: str
    description: str
    query: str
    latency_seconds: float
    token_usage: dict
    rules_passed: int
    rules_total: int
    rule_assertions: list[RuleAssertion]
    judge_score: Optional[JudgeScore] = None
    overall_verdict: Literal["PASS", "FAIL"]


class BenchmarkSummary(BaseModel):
    """Overall benchmark evaluation report across all test cases."""

    timestamp: str
    provider: str
    model: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_percent: float
    rule_pass_rate_percent: float
    average_faithfulness: float
    average_sop_compliance: float
    average_actionability: float
    average_judge_score: float
    total_tokens: int
    average_latency_seconds: float
    results: list[TestCaseResult]
