"""Fail-closed quality gate (requirements R3.2).

Runs every DQ-* rule over the synthetic extracts. On any failure the gate
records the catalogued action (quarantine / block / etc.), opens a steward
issue, and — for DQ-CUS-001 and DQ-HR-001 — marks the asset not_fit_for_ai. A
failure is never a silent skip: every failing row produces a ``Finding`` with
an issue id.

The result is a :class:`GateResult` the scorecard and (later) the label export
consume. Standard-library only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .. import synthdata
from . import registry, rules

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW = os.path.join(REPO_ROOT, "data", "raw")
REFERENCE = os.path.join(REPO_ROOT, "data", "reference")


@dataclass
class Finding:
    rule_id: str
    severity: str
    record_key: str
    actions: tuple[str, ...]
    issue_id: str
    message: str


@dataclass
class GateResult:
    findings: list[Finding] = field(default_factory=list)
    checked: int = 0  # number of (rule, record) evaluations

    @property
    def passed(self) -> bool:
        return not self.findings

    def for_rule(self, rule_id: str) -> list[Finding]:
        return [f for f in self.findings if f.rule_id == rule_id]

    @property
    def blocked_products(self) -> set[str]:
        out = set()
        for f in self.findings:
            if "block_product" in f.actions:
                out.add(registry.get(f.rule_id).domain)
        return out


def _issue_id(rule_id: str, key: str) -> str:
    return f"ISS-{rule_id}-{key}"


def run_gate() -> GateResult:
    result = GateResult()
    _check_customer(result)
    _check_product(result)
    _check_finance(result)
    _check_hr(result)
    return result


def _record(result: GateResult, rule_id: str, key: str, message: str) -> None:
    rule = registry.get(rule_id)
    result.findings.append(
        Finding(
            rule_id=rule_id,
            severity=rule.severity,
            record_key=key,
            actions=rule.actions,
            issue_id=_issue_id(rule_id, key),
            message=message,
        )
    )


def _check_customer(result: GateResult) -> None:
    rows = synthdata.read_csv(os.path.join(RAW, "customer", "customers.csv"))
    duplicates = rules.customer_ids_unique(rows)
    reported_dup: set[str] = set()
    for i, row in enumerate(rows):
        key = f"{row.get('customer_id', '?')}@{row.get('company', '?')}#{i}"
        result.checked += 3
        if not rules.customer_email_valid(row):
            _record(result, "DQ-CUS-001", key, "email missing or invalid")
        # DQ-CUS-002 is a dataset-scope rule: report each duplicated key once.
        cid = (row.get("customer_id") or "").strip()
        if not rules.customer_id_row_ok(row, duplicates) and cid not in reported_dup:
            reported_dup.add(cid or key)
            _record(result, "DQ-CUS-002", cid or key,
                    "customer_id missing or duplicated across companies")
        if not rules.customer_vat_valid(row):
            _record(result, "DQ-CUS-003", key, "vat_id violates contract pattern")


def _check_product(result: GateResult) -> None:
    rows = synthdata.read_csv(os.path.join(RAW, "product", "products.csv"))
    for i, row in enumerate(rows):
        key = f"{row.get('product_id', '?')}#{i}"
        result.checked += 1
        if not rules.product_mandatory_present(row):
            _record(result, "DQ-PRD-001", key, "mandatory product attribute missing")


def _check_finance(result: GateResult) -> None:
    postings = synthdata.read_csv(os.path.join(RAW, "finance", "finance_postings.csv"))
    totals = synthdata.read_csv(os.path.join(RAW, "finance", "finance_control_totals.csv"))
    ref = synthdata.read_csv(os.path.join(REFERENCE, "finance_company_codes.csv"))
    for i, row in enumerate(postings):
        key = f"{row.get('posting_id', '?')}#{i}"
        result.checked += 1
        if not rules.finance_cost_centre_valid(row, ref):
            _record(result, "DQ-FIN-001", key, "cost_centre_id missing/unknown/inactive")
    # Consistency: a company whose reported total does not reconcile also fails
    # DQ-FIN-001 (the catalog lists consistency/referential integrity together).
    for company in sorted({r["company"] for r in postings}):
        result.checked += 1
        if not rules.finance_reconciles(company, postings, totals):
            _record(result, "DQ-FIN-001", f"reconcile:{company}",
                    "reported total does not reconcile with postings")


def _check_hr(result: GateResult) -> None:
    rows = synthdata.read_csv(os.path.join(RAW, "hr", "employees.csv"))
    for i, row in enumerate(rows):
        key = f"{row.get('employee_id', '?')}#{i}"
        result.checked += 1
        if not rules.hr_record_current(row):
            _record(result, "DQ-HR-001", key, "HR record outside currentness window")
