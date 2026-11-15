"""Lineage accessor (requirements R2.2).

Reads ``dbt/lineage.yaml`` and answers lineage questions for the report and the
catalog: which source feeds each KPI dataset, which mart builds it, and which
DQ-* rules guard it. v1 lineage coverage is binary (yes/no on the declared
datasets).
"""

from __future__ import annotations

import os

from . import yaml_min

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE_FILE = os.path.join(REPO_ROOT, "dbt", "lineage.yaml")

DOMAINS = ("Customer", "Product", "Finance", "HR")


def load() -> list[dict]:
    data = yaml_min.load_file(LINEAGE_FILE)
    return data["datasets"]


def by_domain() -> dict[str, dict]:
    return {ds["domain"]: ds for ds in load()}


def coverage_complete() -> bool:
    """True when every declared domain has a KPI dataset with a source and mart."""
    mapped = by_domain()
    for domain in DOMAINS:
        ds = mapped.get(domain)
        if not ds or not ds.get("source") or not ds.get("mart") or not ds.get("kpi"):
            return False
    return True
