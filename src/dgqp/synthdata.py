"""Deterministic synthetic extracts for the four Tarsfeld domains.

Synthetic data only. Fictional firms. HR is the most sensitive domain and is
local-only (it is never configured for an Azure source). Two country companies:
``DE01`` (German HQ) and ``AT01`` (one other country company).

The extracts are intentionally dirty so the demo can show each ``DQ-*`` rule
failing and a steward cleanse. The seeded defects are documented in
``data/DEFECTS.md`` and asserted by ``tests/test_phase1_data.py``.

This module writes CSV using only the standard library so it runs offline.
"""

from __future__ import annotations

import csv
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(REPO_ROOT, "data", "raw")
REFERENCE = os.path.join(REPO_ROOT, "data", "reference")

COMPANIES = ("DE01", "AT01")


# --- row sets (small, hand-built, defects clearly commented) --------------

def customer_rows() -> list[dict]:
    return [
        # clean baseline
        {"customer_id": "C-DE-1001", "company": "DE01", "name": "Alpha GmbH",
         "email": "contact@alpha.example", "vat_id": "DE111111111"},
        {"customer_id": "C-DE-1002", "company": "DE01", "name": "Beta AG",
         "email": "hello@beta.example", "vat_id": "DE222222222"},
        {"customer_id": "C-AT-2001", "company": "AT01", "name": "Gamma GmbH",
         "email": "office@gamma.example", "vat_id": "ATU33333333"},
        # DQ-CUS-001: missing / invalid email
        {"customer_id": "C-DE-1003", "company": "DE01", "name": "Delta KG",
         "email": "", "vat_id": "DE444444444"},
        {"customer_id": "C-AT-2002", "company": "AT01", "name": "Epsilon GmbH",
         "email": "not-an-email", "vat_id": "ATU55555555"},
        # DQ-CUS-002: duplicate customer_id across companies (same key reused)
        {"customer_id": "C-DE-1001", "company": "AT01", "name": "Alpha Austria",
         "email": "at@alpha.example", "vat_id": "ATU66666666"},
        # DQ-CUS-003: VAT present but violates the contract per-country pattern
        {"customer_id": "C-DE-1004", "company": "DE01", "name": "Zeta GmbH",
         "email": "z@zeta.example", "vat_id": "DE12AB"},
        # DQ-CUS-003 allowed: empty VAT where contract permits (not VAT-registered)
        {"customer_id": "C-AT-2003", "company": "AT01", "name": "Eta Verein",
         "email": "e@eta.example", "vat_id": ""},
    ]


def product_rows() -> list[dict]:
    return [
        {"product_id": "P-100", "company": "DE01", "name": "Widget",
         "status": "active", "unit_of_measure": "EA"},
        {"product_id": "P-101", "company": "DE01", "name": "Gadget",
         "status": "active", "unit_of_measure": "EA"},
        {"product_id": "P-200", "company": "AT01", "name": "Sprocket",
         "status": "active", "unit_of_measure": "KG"},
        # DQ-PRD-001: missing mandatory attributes (name, unit_of_measure)
        {"product_id": "P-102", "company": "DE01", "name": "",
         "status": "active", "unit_of_measure": ""},
        # DQ-PRD-001: missing status
        {"product_id": "P-201", "company": "AT01", "name": "Flange",
         "status": "", "unit_of_measure": "EA"},
    ]


def finance_rows() -> list[dict]:
    # Finance postings reference cost centres. A reconciliation defect is seeded:
    # the two postings for DE01 total 300.00, but the reported control total is
    # 350.00 (does not reconcile) — see finance_control_totals().
    return [
        {"posting_id": "F-1", "company": "DE01", "cost_centre_id": "CC-1000",
         "amount": "100.00"},
        {"posting_id": "F-2", "company": "DE01", "cost_centre_id": "CC-1001",
         "amount": "200.00"},
        {"posting_id": "F-3", "company": "AT01", "cost_centre_id": "CC-2000",
         "amount": "150.00"},
        # DQ-FIN-001: cost_centre_id not in reference list for the company
        {"posting_id": "F-4", "company": "DE01", "cost_centre_id": "CC-9999",
         "amount": "75.00"},
        # DQ-FIN-001: cost_centre_id exists but is inactive
        {"posting_id": "F-5", "company": "AT01", "cost_centre_id": "CC-2001",
         "amount": "50.00"},
    ]


def finance_control_totals() -> list[dict]:
    # Reported totals used for the consistency/reconciliation check. DE01 does
    # not reconcile with the sum of its postings on purpose.
    # AT01 reconciles (F-3 150.00 + F-5 50.00 = 200.00). DE01 does not: its
    # postings sum to 300.00 (F-1 + F-2) but the reported total is 350.00. Only
    # DE01 is the seeded reconciliation defect (see data/DEFECTS.md).
    return [
        {"company": "DE01", "reported_total": "350.00"},
        {"company": "AT01", "reported_total": "200.00"},
    ]


def cost_centre_reference() -> list[dict]:
    return [
        {"cost_centre_id": "CC-1000", "company": "DE01", "active": "true"},
        {"cost_centre_id": "CC-1001", "company": "DE01", "active": "true"},
        {"cost_centre_id": "CC-2000", "company": "AT01", "active": "true"},
        {"cost_centre_id": "CC-2001", "company": "AT01", "active": "false"},
    ]


def hr_rows() -> list[dict]:
    # HR currentness window is a contract parameter (see hr contract). These
    # dates are relative to a fixed reference "today" used by DQ-HR-001 so the
    # synthetic set is deterministic.
    return [
        {"employee_id": "E-1", "company": "DE01", "status": "active",
         "effective_from": "2022-01-01", "effective_to": "",
         "last_verified_on": "2026-10-01"},
        {"employee_id": "E-2", "company": "AT01", "status": "active",
         "effective_from": "2023-03-15", "effective_to": "",
         "last_verified_on": "2026-09-20"},
        # DQ-HR-001: last_verified_on outside currentness window (stale)
        {"employee_id": "E-3", "company": "DE01", "status": "active",
         "effective_from": "2021-06-01", "effective_to": "",
         "last_verified_on": "2024-01-01"},
        # DQ-HR-001: leaver without effective_to
        {"employee_id": "E-4", "company": "AT01", "status": "leaver",
         "effective_from": "2020-02-01", "effective_to": "",
         "last_verified_on": "2026-10-10"},
        # DQ-HR-001: missing status
        {"employee_id": "E-5", "company": "DE01", "status": "",
         "effective_from": "2024-05-01", "effective_to": "",
         "last_verified_on": "2026-10-05"},
    ]


DATASETS = {
    ("customer", "customers.csv"): customer_rows,
    ("product", "products.csv"): product_rows,
    ("finance", "finance_postings.csv"): finance_rows,
    ("finance", "finance_control_totals.csv"): finance_control_totals,
    ("hr", "employees.csv"): hr_rows,
}


def _write_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate() -> list[str]:
    """Write all synthetic extracts and the reference list; return their paths."""
    written: list[str] = []
    for (domain, filename), builder in DATASETS.items():
        path = os.path.join(RAW, domain, filename)
        _write_csv(path, builder())
        written.append(path)
    ref = os.path.join(REFERENCE, "finance_company_codes.csv")
    _write_csv(ref, cost_centre_reference())
    written.append(ref)
    return written


def read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    for p in generate():
        print(os.path.relpath(p, REPO_ROOT))
