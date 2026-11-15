"""Phase 6 — steward issue / cleanse workflow (requirements R6).

* a failed row opens a steward issue carrying rule id, record key, severity,
  timestamp
* end-to-end fail -> issue -> decision -> cleanse -> re-run -> pass, closing the
  issue
* the exception path is explicit and auditable and does NOT silently pass the
  rule
* a decision must carry an auditable note
* the issue-cycle process metric is recorded (counts only, no fabricated timing)
"""

import pytest

from dgqp import workflow
from dgqp.quality import rules


def _ref():
    return [
        {"cost_centre_id": "CC-1000", "company": "DE01", "active": "true"},
        {"cost_centre_id": "CC-9999", "company": "DE01", "active": "false"},
    ]


def test_open_issue_captures_rule_key_severity_time():
    log = workflow.WorkflowLog()
    issue = log.open_issue("DQ-CUS-001", "C-DE-1003@DE01", "email invalid",
                           now="2026-11-15T10:00:00Z")
    assert issue.rule_id == "DQ-CUS-001"
    assert issue.record_key == "C-DE-1003@DE01"
    assert issue.severity == "high"
    assert issue.opened_at == "2026-11-15T10:00:00Z"
    assert issue.state == workflow.OPEN


def test_cleanse_loop_customer_email_resolves_and_closes():
    # A malformed email fails DQ-CUS-001; the documented cleanse nulls it and the
    # rule is re-run. (An empty email still fails presence, so for a true PASS we
    # provide a verified value via a custom cleanse.)
    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    bad = {"customer_id": "C-AT-2002", "company": "AT01", "email": "not-an-email"}

    def cleanse_with_verified_value(row):
        fixed = dict(row)
        fixed["email"] = "verified@example.org"  # steward sources a real value
        return fixed

    issue = rem.remediate(
        rule_id="DQ-CUS-001", record_key="C-AT-2002@AT01",
        message="email invalid", row=bad,
        decision=workflow.CLEANSE, note="Steward confirmed address with customer",
        cleanse=cleanse_with_verified_value,
        check=rules.customer_email_valid,
        clock=lambda: "2026-11-15T10:00:00Z",
    )
    assert issue.state == workflow.CLOSED
    assert issue.decision == workflow.CLEANSE
    assert issue.rerun_passed is True


def test_cleanse_loop_finance_cost_centre_resolves():
    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    ref = _ref()
    bad = {"posting_id": "F-4", "company": "DE01", "cost_centre_id": "CC-XXXX", "amount": "75.00"}

    issue = rem.remediate(
        rule_id="DQ-FIN-001", record_key="F-4",
        message="cost centre unknown", row=bad,
        decision=workflow.CLEANSE, note="Re-keyed to active CC-1000 per GL",
        cleanse=lambda r: workflow.cleanse_finance_cost_centre(r, "CC-1000"),
        check=lambda r: rules.finance_cost_centre_valid(r, ref),
        clock=lambda: "2026-11-15T10:05:00Z",
    )
    assert issue.rerun_passed is True
    assert issue.state == workflow.CLOSED


def test_exception_path_is_auditable_and_not_a_silent_pass():
    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    bad = {"product_id": "P-102", "company": "DE01", "name": "",
           "status": "active", "unit_of_measure": ""}

    issue = rem.remediate(
        rule_id="DQ-PRD-001", record_key="P-102",
        message="mandatory attrs missing", row=bad,
        decision=workflow.EXCEPTION,
        note="Discontinued SKU; retained for audit, not published",
        cleanse=None,
        check=rules.product_mandatory_present,
        clock=lambda: "2026-11-15T10:10:00Z",
    )
    assert issue.decision == workflow.EXCEPTION
    assert issue.decision_note  # auditable
    assert issue.rerun_passed is False  # not silently passed
    assert issue.state == workflow.CLOSED


def test_decision_requires_a_note():
    log = workflow.WorkflowLog()
    issue = log.open_issue("DQ-PRD-001", "P-102", "missing", now="t")
    with pytest.raises(ValueError):
        log.record_decision(issue, workflow.CLEANSE, note="   ")


def test_unknown_decision_rejected():
    log = workflow.WorkflowLog()
    issue = log.open_issue("DQ-PRD-001", "P-102", "missing", now="t")
    with pytest.raises(ValueError):
        log.record_decision(issue, "ignore", note="x")


def test_cleanse_does_not_mutate_source_row():
    row = {"email": "not-an-email"}
    workflow.cleanse_customer_email(row)
    assert row["email"] == "not-an-email"  # original untouched


def test_issue_cycle_metrics_counts_only():
    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    ref = _ref()
    rem.remediate(
        "DQ-FIN-001", "F-4", "cc unknown",
        {"company": "DE01", "cost_centre_id": "CC-X", "amount": "1"},
        workflow.CLEANSE, "re-keyed",
        lambda r: workflow.cleanse_finance_cost_centre(r, "CC-1000"),
        lambda r: rules.finance_cost_centre_valid(r, ref),
        clock=lambda: "t",
    )
    rem.remediate(
        "DQ-PRD-001", "P-102", "missing",
        {"product_id": "P", "name": "", "status": "a", "unit_of_measure": ""},
        workflow.EXCEPTION, "discontinued", None,
        rules.product_mandatory_present, clock=lambda: "t",
    )
    metrics = workflow.issue_cycle_metrics(log)
    assert metrics["issues_opened"] == 2
    assert metrics["issues_closed"] == 2
    assert metrics["cleansed_resolved"] == 1
    assert metrics["exceptions_recorded"] == 1
    # counts only; no fabricated duration
    assert "duration" not in metrics


def test_workflow_cli_demo_runs_and_resolves():
    from dgqp import workflow_cli
    assert workflow_cli.main() == 0  # fail -> issue -> cleanse -> re-run passes
