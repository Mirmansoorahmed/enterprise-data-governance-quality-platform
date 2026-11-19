"""DQ-* rule check functions.

Each function encodes exactly one catalogued rule from
``docs/RULES-AND-POLICIES.md`` and returns ``True`` when the row passes. The
contract parameters (email pattern, VAT per-country pattern, HR currentness
window) are read from the ODCS contracts, not hard-coded here, so the contract
stays the source of truth.

Standard-library only.
"""

from __future__ import annotations

import datetime as _dt
import os
import re

from .. import yaml_min

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONTRACTS = os.path.join(REPO_ROOT, "contracts")

_CONTRACT_CACHE: dict[str, dict] = {}


def _contract(name: str) -> dict:
    if name not in _CONTRACT_CACHE:
        _CONTRACT_CACHE[name] = yaml_min.load_file(os.path.join(CONTRACTS, name))
    return _CONTRACT_CACHE[name]


def _email_pattern() -> str:
    for table in _contract("customer.odcs.yaml")["schema"]:
        for prop in table["properties"]:
            if prop["name"] == "email":
                return prop["pattern"]
    raise KeyError("email pattern not found in customer contract")


def _vat_patterns() -> dict:
    return _contract("customer.odcs.yaml")["customProperties"]["vatPatterns"]


def _hr_params() -> tuple[int, _dt.date]:
    cp = _contract("hr.odcs.yaml")["customProperties"]
    window = int(cp["currentnessWindowDays"])
    ref = _dt.date.fromisoformat(str(cp["currentnessReferenceDate"]))
    return window, ref


# --- DQ-CUS-001 -----------------------------------------------------------

def customer_email_valid(row: dict) -> bool:
    email = (row.get("email") or "").strip()
    if not email:
        return False
    return re.match(_email_pattern(), email) is not None


# --- DQ-CUS-002 (evaluated across the whole customer set) -----------------

def customer_ids_unique(rows: list[dict]) -> set[str]:
    """Return the set of ``customer_id`` values that are duplicated."""
    seen: dict[str, int] = {}
    for row in rows:
        cid = row.get("customer_id", "")
        seen[cid] = seen.get(cid, 0) + 1
    return {cid for cid, n in seen.items() if cid and n > 1}


def customer_id_row_ok(row: dict, duplicates: set[str]) -> bool:
    cid = (row.get("customer_id") or "").strip()
    if not cid:
        return False
    return cid not in duplicates


# --- DQ-CUS-003 -----------------------------------------------------------

def customer_vat_valid(row: dict) -> bool:
    vat = (row.get("vat_id") or "").strip()
    if not vat:
        return True  # empty allowed where contract permits (not VAT-registered)
    patterns = _vat_patterns()
    for _country, pattern in patterns.items():
        if re.match(pattern, vat):
            return True
    return False


# --- DQ-PRD-001 -----------------------------------------------------------

def product_mandatory_present(row: dict) -> bool:
    for field in ("product_id", "name", "status", "unit_of_measure"):
        if not (row.get(field) or "").strip():
            return False
    return True


# --- DQ-FIN-001 -----------------------------------------------------------

def finance_cost_centre_valid(row: dict, reference: list[dict]) -> bool:
    cc = (row.get("cost_centre_id") or "").strip()
    company = row.get("company", "")
    if not cc:
        return False
    for ref in reference:
        if ref["cost_centre_id"] == cc and ref["company"] == company:
            return str(ref["active"]).lower() == "true"
    return False


def finance_reconciles(company: str, postings: list[dict], control_totals: list[dict]) -> bool:
    posting_sum = sum(
        float(r["amount"]) for r in postings if r["company"] == company
    )
    for row in control_totals:
        if row["company"] == company:
            return abs(float(row["reported_total"]) - posting_sum) < 0.001
    return False


# --- DQ-HR-001 ------------------------------------------------------------

def hr_record_current(row: dict) -> bool:
    if not (row.get("status") or "").strip():
        return False
    if not (row.get("effective_from") or "").strip():
        return False
    last = (row.get("last_verified_on") or "").strip()
    if not last:
        return False
    if (row.get("status") or "").strip().lower() == "leaver" and not (
        row.get("effective_to") or ""
    ).strip():
        return False
    window_days, ref_date = _hr_params()
    try:
        verified = _dt.date.fromisoformat(last)
    except ValueError:
        return False
    return (ref_date - verified).days <= window_days
