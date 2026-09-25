import json
from typing import Any
from schema import ExecutionLogItem, RetentionActionItem


def execute_action(action: RetentionActionItem, customer: str) -> ExecutionLogItem:
    """Simulate dispatching concrete side-effects to external enterprise systems."""
    a_type = action.action_type

    if a_type == "DEVOPS_INCIDENT":
        target = "PagerDuty & Jira Service Desk"
        payload = {
            "project": "DEV",
            "priority": "P1",
            "summary": f"[CRITICAL CHURN BLOCKER] {customer}: {action.title}",
            "assignee_role": action.owner_role,
            "description": action.description,
            "sla_hours": 4,
        }
        msg = f"Dispatched P1 Incident to {target}. SLA: 4 hours."

    elif a_type == "FINANCE_PAYOUT_RELEASE":
        target = "Fintech Settlement Engine & Core Banking"
        payload = {
            "account": customer,
            "amount_idr": action.cost_idr,
            "authorization": "CHURN_PREVENTION_EMERGENCY_RELEASE",
            "reference": f"PAYOUT-REL-{customer.replace(' ', '-').upper()}",
            "note": action.description,
        }
        msg = f"Unfroze settlement payout of Rp {action.cost_idr:,.0f} via {target}."

    elif a_type == "FEE_WAIVER_OR_DISCOUNT":
        target = "Billing & Subscription Gateway"
        payload = {
            "customer": customer,
            "credit_value_idr": action.cost_idr,
            "type": "PLATFORM_FEE_WAIVER",
            "notes": action.description,
        }
        msg = f"Applied platform fee credit / waiver valued at Rp {action.cost_idr:,.0f}."

    elif a_type == "COMMERCIAL_RENEGOTIATION":
        target = "Salesforce Enterprise CRM"
        payload = {
            "account": customer,
            "stage": "CONTRACT_RENEGOTIATION",
            "lead": action.owner_role,
            "notes": action.description,
        }
        msg = f"Logged high-priority commercial contract renegotiation in {target}."

    elif a_type == "ACCOUNT_OFFBOARDING":
        target = "Customer Marketing Hub & Account Registry"
        payload = {
            "account": customer,
            "marketing_status": "SUPPRESSED",
            "status": "GRACEFUL_OFFBOARDING",
            "reason": action.description,
        }
        msg = f"Halted active campaigns and initiated offboarding workflow in {target}."

    else:  # Default CRM_OUTREACH
        target = "Zendesk & CRM Outreach Module"
        payload = {
            "customer": customer,
            "task": action.title,
            "assigned_to": action.owner_role,
            "instructions": action.description,
        }
        msg = f"Created high-touch outreach task in {target}."

    return ExecutionLogItem(
        action_type=a_type,
        target_system=target,
        payload=payload,
        status="DISPATCHED",
        message=msg,
    )
