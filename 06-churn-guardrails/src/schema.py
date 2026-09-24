from typing import Literal, Optional
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """Operational retention task with ownership and SLA."""

    action: str = Field(
        ...,
        description="Actionable operational step to mitigate churn risk.",
    )
    priority: Literal["URGENT", "HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description="Priority level based on churn risk severity.",
    )
    sla: str = Field(
        ...,
        description="Target resolution SLA window.",
    )
    owner_role: str = Field(
        ...,
        description="Role responsible for task execution.",
    )


class AccountEvaluation(BaseModel):
    """Strictly validated evaluation for a merchant account."""

    merchant_name: str = Field(
        ...,
        description="Name of the evaluated merchant account.",
    )
    risk_tier: Literal["HIGH", "MEDIUM", "LOW", "NO RISK"] = Field(
        ...,
        description="Categorical risk tier based on activity and ML predictions.",
    )
    churn_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated churn probability score between 0.0 and 1.0.",
    )
    primary_drivers: list[str] = Field(
        ...,
        min_length=1,
        description="Key behavioral trends and usage metrics driving the assessment.",
    )
    recommended_actions: list[ActionItem] = Field(
        ...,
        min_length=1,
        description="Prioritized operational intervention steps.",
    )
    proposed_incentive: str = Field(
        ...,
        description="Commercial or platform incentive recommended to retain the merchant.",
    )
    executive_summary: str = Field(
        ...,
        description="Concise executive briefing for operational dashboards.",
    )


class GuardedAuditResponse(BaseModel):
    """Top-level response contract with guardrail inspection metadata."""

    is_valid_domain: bool = Field(
        ...,
        description="True if the query pertains to customer churn and retention; False if rejected.",
    )
    guardrail_status: Literal["PASSED", "SANITIZED", "BLOCKED"] = Field(
        ...,
        description="Guardrail inspection result: PASSED (clean), SANITIZED (injection stripped), or BLOCKED (off-topic).",
    )
    guardrail_notice: Optional[str] = Field(
        default=None,
        description="Explanation of any filtered instructions or prompt injection attempts.",
    )
    sanitized_query: str = Field(
        ...,
        description="The clean domain query evaluated by the system.",
    )
    evaluations: list[AccountEvaluation] = Field(
        default_factory=list,
        description="List of account evaluations. Empty if the query was BLOCKED.",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Reason for rejection if the query was BLOCKED.",
    )
