import json
from schema import PipelineOutput, RuleAssertion


def evaluate_rules(output: PipelineOutput, test_case: dict) -> list[RuleAssertion]:
    """Execute programmatic, deterministic assertions against pipeline output."""
    assertions = []

    # 1. Domain validity match
    expected_domain = test_case.get("expected_domain", True)
    domain_ok = (output.is_valid_domain == expected_domain)
    assertions.append(
        RuleAssertion(
            name="domain_validity_match",
            passed=domain_ok,
            message=f"is_valid_domain={output.is_valid_domain}, expected={expected_domain}",
        )
    )

    # 2. Guardrail status check
    expected_status = test_case.get("expected_guardrail_status")
    if expected_status:
        status_ok = (output.guardrail_status == expected_status)
        assertions.append(
            RuleAssertion(
                name="guardrail_status_match",
                passed=status_ok,
                message=f"guardrail_status={output.guardrail_status}, expected={expected_status}",
            )
        )

    # 3. Forbidden tokens check (Anti-Leakage)
    forbidden = test_case.get("forbidden_tokens", [])
    raw_json = output.model_dump_json().lower()
    leaked = [t for t in forbidden if t.lower() in raw_json]
    assertions.append(
        RuleAssertion(
            name="forbidden_tokens_absence",
            passed=len(leaked) == 0,
            message="No leaked tokens." if not leaked else f"Leaked forbidden tokens: {leaked}",
        )
    )

    # If the case was expected to be blocked, stop here (no evaluations expected)
    if not expected_domain or output.guardrail_status == "BLOCKED":
        blocked_clean = (len(output.evaluations) == 0 and bool(output.rejection_reason))
        assertions.append(
            RuleAssertion(
                name="blocked_payload_integrity",
                passed=blocked_clean,
                message="Blocked case returned zero evaluations with valid rejection reason."
                if blocked_clean
                else "Blocked case produced unexpected evaluations or missing reason.",
            )
        )
        return assertions

    # 4. Merchant coverage check
    expected_merchants = test_case.get("expected_merchants", [])
    evaluated_names = [e.merchant_name.lower() for e in output.evaluations]
    missing = [m for m in expected_merchants if m.lower() not in evaluated_names]
    assertions.append(
        RuleAssertion(
            name="merchant_coverage",
            passed=len(missing) == 0,
            message="All expected merchants present."
            if not missing
            else f"Missing expected merchants: {missing}",
        )
    )

    # 5. Probability range & bounds integrity
    prob_ok = True
    prob_msgs = []
    min_prob = test_case.get("min_probability")
    max_prob = test_case.get("max_probability")

    for e in output.evaluations:
        if not (0.0 <= e.churn_probability <= 1.0):
            prob_ok = False
            prob_msgs.append(f"{e.merchant_name} probability {e.churn_probability} out of [0, 1]")
        if min_prob is not None and e.churn_probability < min_prob:
            prob_ok = False
            prob_msgs.append(f"{e.merchant_name} probability {e.churn_probability:.2f} < min {min_prob}")
        if max_prob is not None and e.churn_probability > max_prob:
            prob_ok = False
            prob_msgs.append(f"{e.merchant_name} probability {e.churn_probability:.2f} > max {max_prob}")

    assertions.append(
        RuleAssertion(
            name="probability_bounds_integrity",
            passed=prob_ok,
            message="All probabilities valid." if prob_ok else "; ".join(prob_msgs),
        )
    )

    # 6. Risk tier and SLA consistency
    tier_sla_ok = True
    tier_msgs = []
    for e in output.evaluations:
        if e.risk_tier == "HIGH":
            has_urgent_action = any(
                ("24" in a.sla or "urgent" in a.sla.lower() or a.priority == "URGENT")
                for a in e.recommended_actions
            )
            if not has_urgent_action:
                tier_sla_ok = False
                tier_msgs.append(f"{e.merchant_name} is HIGH risk but lacks urgent (<=24h) action SLA")

    assertions.append(
        RuleAssertion(
            name="tier_sla_alignment",
            passed=tier_sla_ok,
            message="Tier and action SLAs properly aligned." if tier_sla_ok else "; ".join(tier_msgs),
        )
    )

    return assertions
