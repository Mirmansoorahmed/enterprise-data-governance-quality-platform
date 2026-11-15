"""Domain marts and one KPI dataset per domain (Phase 2, requirements R2).

dbt is the declarative tool of record for marts and lineage (skeleton under
``dbt/``). The offline CI sandbox has no dbt, so these standard-library
transforms are the documented unit equivalent (design s10): they build the same
one-KPI-per-domain marts and record lineage, and they enforce that a
``DQ-FIN-001`` failing row is held out of the finance mart and its KPI (R2.3).

Each builder returns ``(kpi_rows, held_rows)`` so a caller (and the scorecard)
can see both the published KPI and what the gate held back.
"""

from __future__ import annotations

import os

from . import synthdata
from .quality import rules as dq

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(REPO_ROOT, "data", "raw")
REFERENCE = os.path.join(REPO_ROOT, "data", "reference")


def _read(domain: str, filename: str) -> list[dict]:
    return synthdata.read_csv(os.path.join(RAW, domain, filename))


# --- Customer KPI: active customers with a valid contact email per company --

def customer_kpi() -> tuple[list[dict], list[dict]]:
    rows = _read("customer", "customers.csv")
    reachable, held = [], []
    for row in rows:
        if dq.customer_email_valid(row):
            reachable.append(row)
        else:
            held.append(row)
    counts: dict[str, int] = {}
    for row in reachable:
        counts[row["company"]] = counts.get(row["company"], 0) + 1
    kpi = [
        {"company": c, "reachable_customers": n} for c, n in sorted(counts.items())
    ]
    return kpi, held


# --- Product KPI: count of complete product masters per company -----------

def product_kpi() -> tuple[list[dict], list[dict]]:
    rows = _read("product", "products.csv")
    complete, held = [], []
    for row in rows:
        if dq.product_mandatory_present(row):
            complete.append(row)
        else:
            held.append(row)
    counts: dict[str, int] = {}
    for row in complete:
        counts[row["company"]] = counts.get(row["company"], 0) + 1
    kpi = [
        {"company": c, "complete_products": n} for c, n in sorted(counts.items())
    ]
    return kpi, held


# --- Finance KPI: spend per company, holding out DQ-FIN-001 failures ------

def finance_kpi() -> tuple[list[dict], list[dict]]:
    postings = _read("finance", "finance_postings.csv")
    ref = synthdata.read_csv(os.path.join(REFERENCE, "finance_company_codes.csv"))
    loaded, held = [], []
    for row in postings:
        if dq.finance_cost_centre_valid(row, ref):
            loaded.append(row)
        else:
            # R2.3: a DQ-FIN-001 failing row is blocked from the mart and KPI.
            held.append(row)
    spend: dict[str, float] = {}
    for row in loaded:
        spend[row["company"]] = spend.get(row["company"], 0.0) + float(row["amount"])
    kpi = [
        {"company": c, "spend_from_valid_postings": round(v, 2)}
        for c, v in sorted(spend.items())
    ]
    return kpi, held


# --- HR KPI: count of current, fit-for-use employee records per company ----

def hr_kpi() -> tuple[list[dict], list[dict]]:
    rows = _read("hr", "employees.csv")
    current, held = [], []
    for row in rows:
        if dq.hr_record_current(row):
            current.append(row)
        else:
            held.append(row)
    counts: dict[str, int] = {}
    for row in current:
        counts[row["company"]] = counts.get(row["company"], 0) + 1
    kpi = [
        {"company": c, "current_employees": n} for c, n in sorted(counts.items())
    ]
    return kpi, held


KPI_BUILDERS = {
    "customer": customer_kpi,
    "product": product_kpi,
    "finance": finance_kpi,
    "hr": hr_kpi,
}


def build_all() -> dict[str, dict]:
    """Build every domain KPI; return ``{domain: {kpi, held}}``."""
    out = {}
    for domain, builder in KPI_BUILDERS.items():
        kpi, held = builder()
        out[domain] = {"kpi": kpi, "held": held}
    return out
