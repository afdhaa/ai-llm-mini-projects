from typing import Literal
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """Operational action item prescribed for account retention."""

    action: str = Field(
        ...,
        description="Actionable operational step to mitigate churn risk.",
    )
    priority: Literal["URGENT", "HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        description="Execution priority level based on risk severity.",
    )
    sla: str = Field(
        ...,
        description="Target resolution SLA window (e.g., 'Within 24 hours', '3 business days').",
    )
    owner_role: str = Field(
        ...,
        description="Role responsible for executing the action (e.g., 'Senior Account Manager').",
    )


class ChurnAssessment(BaseModel):
    """Structured, type-safe customer churn evaluation."""

    merchant_name: str = Field(
        ...,
        description="Name of the merchant account evaluated.",
    )
    risk_tier: Literal["HIGH", "MEDIUM", "LOW", "NO RISK"] = Field(
        ...,
        description="Categorical risk tier based on activity and ML predictions.",
    )
    churn_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Calibrated churn probability between 0.0 and 1.0.",
    )
    primary_drivers: list[str] = Field(
        ...,
        min_length=1,
        description="Primary behavioral triggers and activity metrics driving the evaluation.",
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
        description="Concise executive summary for operations dashboards.",
    )


class BatchChurnAssessment(BaseModel):
    """Batch container for multi-account structured evaluations."""

    assessments: list[ChurnAssessment] = Field(
        ...,
        description="List of structured churn assessments for all evaluated merchant accounts.",
    )
