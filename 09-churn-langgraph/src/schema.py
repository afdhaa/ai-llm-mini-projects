from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token consumption accounting."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class DiagnosticFindings(BaseModel):
    """Qualitative diagnostic findings from the Technical/Diagnostics Specialist."""
    root_cause: Literal[
        "TECHNICAL_BUG",
        "BILLING_SETTLEMENT",
        "PRICING_COMMERCIAL",
        "SERVICE_QUALITY",
        "ACCOUNT_LIFECYCLE",
        "GENERAL_SATISFIED",
    ] = Field(description="Primary root cause category deduced from customer interactions.")
    technical_severity: Literal[
        "CRITICAL_P1",
        "HIGH_P2",
        "MEDIUM_P3",
        "LOW_P4",
        "NONE",
    ] = Field(description="Urgency of technical or operational blocker.")
    key_blocker: str = Field(description="One-sentence description of the core bottleneck or issue.")
    diagnostic_summary: str = Field(description="Detailed technical/operational analysis of what failed.")
    requires_technical_escalation: bool = Field(description="Whether engineering or DevOps intervention is mandatory.")


class FinancialAssessment(BaseModel):
    """Commercial and financial evaluation from the Finance/Commercial Specialist."""
    customer_tier: str = Field(description="Customer tier (e.g. ENTERPRISE, GROWTH, MICRO).")
    monthly_gmv_idr: float = Field(description="Monthly Gross Merchandise Value in IDR.")
    monthly_revenue_idr: float = Field(description="Platform revenue generated per month in IDR.")
    pending_payout_idr: float = Field(description="Funds currently held or pending settlement in IDR.")
    max_retention_budget_idr: float = Field(description="Maximum authorized retention budget cap.")
    financial_risk_verdict: Literal[
        "HIGH_EXPOSURE",
        "MODERATE_EXPOSURE",
        "LOW_EXPOSURE",
    ] = Field(description="Financial exposure level if account churns.")
    approved_budget_cap_idr: float = Field(description="Strict monetary ceiling for incentives, waivers, or credits.")
    commercial_rationale: str = Field(description="Strategic justification based on merchant LTV and margin economics.")


class RetentionActionItem(BaseModel):
    """Single atomic operational action item in the retention strategy."""
    action_type: Literal[
        "CRM_OUTREACH",
        "DEVOPS_INCIDENT",
        "FINANCE_PAYOUT_RELEASE",
        "FEE_WAIVER_OR_DISCOUNT",
        "COMMERCIAL_RENEGOTIATION",
        "ACCOUNT_OFFBOARDING",
    ] = Field(description="Type of operational side-effect to dispatch.")
    title: str = Field(description="Short action headline.")
    description: str = Field(description="Step-by-step instruction or payload for execution.")
    owner_role: str = Field(description="Department role responsible (e.g. Lead DevOps, Finance Manager).")
    cost_idr: float = Field(default=0.0, description="Estimated direct financial expenditure, waiver, or release value.")
    requires_human_approval: bool = Field(default=False, description="Whether this specific action needs human sign-off.")


class RetentionProposal(BaseModel):
    """Unified retention plan synthesized by the Retention Lead / Supervisor."""
    summary: str = Field(description="Executive summary of the negotiated retention plan.")
    primary_root_cause: str = Field(description="Harmonized root cause agreed upon by agents.")
    total_proposed_cost_idr: float = Field(description="Total monetary sum of proposed discounts/waivers/payouts.")
    is_override_sop: bool = Field(description="Whether the standard playbook SOP was overridden.")
    override_reason: str = Field(description="Explanation for why generic SOP was modified or discarded.")
    action_items: list[RetentionActionItem] = Field(description="Prioritized list of concrete actions.")
    requires_hitl: bool = Field(description="Flag indicating if plan triggers the Human-in-the-Loop gate.")
    hitl_reason: str = Field(description="Condition that triggered human review (e.g., high cost, P1 bug, high risk).")


class ExecutionLogItem(BaseModel):
    """Record of a dispatched operational action."""
    action_type: str
    target_system: str
    payload: dict[str, Any]
    status: Literal["DISPATCHED", "SIMULATED", "SKIPPED", "BLOCKED"]
    message: str


class AgentState(TypedDict):
    """Shared state dictionary tracked across LangGraph nodes."""
    customer_id: str
    transactions: int
    active_days: int
    inactive_days: int
    churn_probability: float
    ml_risk_level: str
    support_tickets: list[dict[str, Any]]
    financials: dict[str, Any]
    sop_baseline: dict[str, Any]
    diagnostic_findings: DiagnosticFindings | None
    financial_assessment: FinancialAssessment | None
    proposal: RetentionProposal | None
    hitl_status: Literal["PENDING_REVIEW", "APPROVED", "REJECTED", "AUTO_APPROVED"]
    human_feedback: str | None
    approved_action_indices: list[int] | None
    execution_logs: list[ExecutionLogItem]
    token_usage: TokenUsage
