"""Steward issue / cleanse workflow (requirements R6).

The business-IT interface: a failed quality-gate row becomes a steward issue;
the steward records a decision (cleanse or exception); a documented cleanse is
applied; the rule is re-run; on resolution the issue closes. An exception is
explicit and auditable.

State machine:  open -> decided(cleanse|exception) -> re-run -> closed

Issues are modelled in memory and can be serialised for the demo and the
issue-cycle process metric. The cleanse operates on a working copy of a row, so
the committed synthetic extracts are never mutated by the workflow. Standard-
library only.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Callable

from .quality import registry


OPEN = "open"
DECIDED = "decided"
CLOSED = "closed"

CLEANSE = "cleanse"
EXCEPTION = "exception"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Issue:
    issue_id: str
    rule_id: str
    severity: str
    record_key: str
    message: str
    opened_at: str
    state: str = OPEN
    decision: str | None = None          # "cleanse" | "exception"
    decision_note: str | None = None
    decided_at: str | None = None
    closed_at: str | None = None
    rerun_passed: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkflowLog:
    issues: list[Issue] = field(default_factory=list)

    def open_issue(self, rule_id: str, record_key: str, message: str,
                    now: str | None = None) -> Issue:
        rule = registry.get(rule_id)
        issue = Issue(
            issue_id=f"ISS-{rule_id}-{record_key}",
            rule_id=rule_id,
            severity=rule.severity,
            record_key=record_key,
            message=message,
            opened_at=now or _now(),
        )
        self.issues.append(issue)
        return issue

    def record_decision(self, issue: Issue, decision: str, note: str,
                        now: str | None = None) -> None:
        if decision not in (CLEANSE, EXCEPTION):
            raise ValueError(f"unknown decision: {decision}")
        if not note.strip():
            raise ValueError("a decision must carry an auditable note")
        issue.decision = decision
        issue.decision_note = note
        issue.decided_at = now or _now()
        issue.state = DECIDED

    def close(self, issue: Issue, rerun_passed: bool, now: str | None = None) -> None:
        issue.rerun_passed = rerun_passed
        issue.closed_at = now or _now()
        issue.state = CLOSED


# --- documented cleanse functions, one per rule where a fix is mechanical --

def cleanse_customer_email(row: dict) -> dict:
    """Documented cleanse: drop an invalid email so the contact is quarantined
    with a null contact rather than a malformed one, pending a verified value.
    Returns a working copy; the source row is not mutated.
    """
    fixed = dict(row)
    email = (fixed.get("email") or "").strip()
    if "@" not in email:
        fixed["email"] = ""  # mark missing; steward will source a verified value
    return fixed


def cleanse_product_mandatory(row: dict, defaults: dict | None = None) -> dict:
    """Documented cleanse: fill a mandatory product attribute from a steward-
    provided value. Without a provided value the row stays incomplete (the
    cleanse cannot invent data).
    """
    fixed = dict(row)
    for field_name, value in (defaults or {}).items():
        if not (fixed.get(field_name) or "").strip():
            fixed[field_name] = value
    return fixed


def cleanse_finance_cost_centre(row: dict, corrected_cost_centre: str) -> dict:
    """Documented cleanse: the steward re-keys the posting to a valid, active
    cost centre."""
    fixed = dict(row)
    fixed["cost_centre_id"] = corrected_cost_centre
    return fixed


@dataclass
class Remediation:
    """One end-to-end remediation: open -> decide -> cleanse -> re-run -> close.

    ``check`` re-runs the rule on the (possibly cleansed) row and returns True
    when it now passes.
    """
    log: WorkflowLog

    def remediate(self, rule_id: str, record_key: str, message: str, row: dict,
                  decision: str, note: str,
                  cleanse: Callable[[dict], dict] | None,
                  check: Callable[[dict], bool],
                  clock: Callable[[], str] | None = None) -> Issue:
        tick = clock or _now
        issue = self.log.open_issue(rule_id, record_key, message, now=tick())
        self.log.record_decision(issue, decision, note, now=tick())
        if decision == CLEANSE:
            if cleanse is None:
                raise ValueError("a cleanse decision needs a cleanse function")
            cleansed = cleanse(row)
            passed = check(cleansed)
            self.log.close(issue, rerun_passed=passed, now=tick())
        else:
            # Exception: no data change; the exception is explicit and auditable
            # (recorded in decision/decision_note). The rule is NOT silently
            # passed; rerun_passed stays False to reflect the data still fails.
            self.log.close(issue, rerun_passed=False, now=tick())
        return issue


def issue_cycle_metrics(log: WorkflowLog) -> dict:
    """Process metrics for the demo run file (not a production SLA).

    Returns counts only; durations in the demo are wall-clock and belong in a
    committed run file, so this does not fabricate a timing.
    """
    closed = [i for i in log.issues if i.state == CLOSED]
    return {
        "issues_opened": len(log.issues),
        "issues_closed": len(closed),
        "cleansed_resolved": sum(
            1 for i in closed if i.decision == CLEANSE and i.rerun_passed
        ),
        "exceptions_recorded": sum(1 for i in closed if i.decision == EXCEPTION),
    }
