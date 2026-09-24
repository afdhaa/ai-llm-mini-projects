from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RootCauseCategory(str, Enum):
    """Categorical classification of customer churn root causes."""

    TECHNICAL_BUG = "TECHNICAL_BUG"
    FINANCIAL_SETTLEMENT = "FINANCIAL_SETTLEMENT"
    PRICING_COMMERCIAL = "PRICING_COMMERCIAL"
    LOGISTICS_OPERATIONAL = "LOGISTICS_OPERATIONAL"
    ACCOUNT_LIFECYCLE = "ACCOUNT_LIFECYCLE"
    FEATURE_LIMITATION = "FEATURE_LIMITATION"
    GENERAL_SATISFIED = "GENERAL_SATISFIED"
class TokenUsage(BaseModel):
    """Token consumption metrics for the LLM synthesis call."""

    prompt_tokens: int = Field(default=0, description="Tokens used for prompt")
    completion_tokens: int = Field(default=0, description="Tokens generated in completion")
    total_tokens: int = Field(default=0, description="Total tokens consumed")




class TicketEvidence(BaseModel):
    """Evidence extracted from retrieved support tickets."""

    ticket_id: str = Field(..., description="ID of the retrieved ticket")
    channel: str = Field(..., description="Channel of the complaint/inquiry (e.g. WhatsApp, Email, Zendesk)")
    timestamp: str = Field(..., description="Date and time of the interaction")
    snippet: str = Field(..., description="Key quote or concise summary of customer's message")
    sentiment: Literal["SEVERELY_DISSATISFIED", "CONCERNED", "NEUTRAL", "POSITIVE"] = Field(
        ..., description="Assessed customer sentiment"
    )
    sentiment_reason: str = Field(
        default="", description="Brief rationale explaining why this sentiment was assigned"
    )


class SopBaselineAction(BaseModel):
    """Baseline action prescribed by standard SOP playbook before RAG context."""

    risk_level: str = Field(..., description="Risk level determined by ML (HIGH, MEDIUM, LOW, NO RISK)")
    sla: str = Field(..., description="Standard SLA window from playbook")
    pic: str = Field(..., description="Standard PIC (Person in Charge) from playbook")
    generic_incentive: str = Field(..., description="Standard voucher / incentive from playbook")
    generic_actions: list[str] = Field(..., description="Default procedural steps from playbook")


class ContextAwareIntervention(BaseModel):
    """Context-aware intervention synthesized from RAG support tickets."""

    primary_root_cause: RootCauseCategory = Field(
        ..., description="The true primary driver of churn inferred from tickets"
    )
    root_cause_explanation: str = Field(
        ..., description="Detailed narrative explaining why the merchant is at risk based on tickets"
    )
    is_sop_adequate: bool = Field(
        ..., description="Whether the generic SOP playbook incentive is adequate or counterproductive"
    )
    override_justification: str = Field(
        ..., description="Why the standard playbook action was overridden, refined, or preserved"
    )
    tailored_action_items: list[str] = Field(
        ..., min_length=1, description="Specific, targeted interventions addressing the actual root cause"
    )
    recommended_pic: str = Field(
        ..., description="Adjusted role responsible (e.g., Tech Support / DevOps vs Commercial Account Manager)"
    )
    urgency: Literal["CRITICAL_IMMEDIATE", "HIGH", "MEDIUM", "LOW_MONITOR"] = Field(
        ..., description="Calibrated operational urgency level"
    )
    ticket_evaluations: list[TicketEvidence] = Field(
        default_factory=list, description="Contextual evaluation of each retrieved ticket"
    )


class ChurnRagReport(BaseModel):
    """Complete end-to-end report combining ML, SOP Playbook, and RAG Context."""

    customer: str = Field(..., description="Target merchant account name")
    transactions: int = Field(..., description="Total transactions in the evaluated period")
    active_days: int = Field(..., description="Days active within evaluated period")
    inactive_days: int = Field(..., description="Days inactive within evaluated period")
    churn_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Calibrated probability from Scikit-Learn model"
    )
    ml_risk_level: Literal["HIGH", "MEDIUM", "LOW", "NO RISK"] = Field(
        ..., description="Risk category based on churn probability"
    )
    sop_baseline: SopBaselineAction = Field(
        ..., description="Baseline recommendation from standard playbook"
    )
    retrieved_tickets: list[TicketEvidence] = Field(
        default_factory=list, description="Relevant support tickets retrieved via semantic search"
    )
    tailored_intervention: ContextAwareIntervention = Field(
        ..., description="Final synthesized context-aware action plan addressing true root causes"
    )
    token_usage: Optional[TokenUsage] = Field(
        default=None, description="Detailed LLM token consumption metrics"
    )
