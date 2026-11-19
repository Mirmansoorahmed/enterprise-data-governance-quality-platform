"""Phase 2 — dbt marts + lineage (requirements R2).

* one KPI dataset per domain builds
* lineage coverage is complete (binary yes) on the declared datasets
* R2.3: a DQ-FIN-001 failing row is held out of the finance mart and its KPI
"""

import os

import pytest

from dgqp import lineage, marts, synthdata
from conftest import REPO_ROOT


@pytest.fixture(scope="module", autouse=True)
def _generate_data():
    synthdata.generate()


def test_all_domains_build_a_kpi():
    built = marts.build_all()
    assert set(built) == {"customer", "product", "finance", "hr"}
    for domain, result in built.items():
        assert result["kpi"], f"{domain} KPI should not be empty"


def test_lineage_coverage_complete():
    assert lineage.coverage_complete() is True
    mapped = lineage.by_domain()
    for domain in lineage.DOMAINS:
        assert mapped[domain]["source"]
        assert mapped[domain]["mart"]


def test_lineage_each_dataset_names_its_rules():
    for ds in lineage.load():
        assert ds["rules"], f"{ds['domain']} KPI must name its DQ-* rules"


def test_fin_001_failing_rows_held_from_mart_and_kpi():
    kpi, held = marts.finance_kpi()
    held_ids = {r["posting_id"] for r in held}
    # F-4 (missing cost centre) and F-5 (inactive) must be held out.
    assert {"F-4", "F-5"} <= held_ids
    # The DE01 spend KPI must exclude the held DE01 posting (F-4 = 75.00).
    de = next((r for r in kpi if r["company"] == "DE01"), None)
    assert de is not None
    assert de["spend_from_valid_postings"] == 300.00  # F-1 + F-2 only


def test_product_kpi_excludes_incomplete():
    kpi, held = marts.product_kpi()
    held_ids = {r["product_id"] for r in held}
    assert {"P-102", "P-201"} <= held_ids


def test_customer_kpi_excludes_invalid_email():
    kpi, held = marts.customer_kpi()
    held_ids = {r["customer_id"] for r in held}
    assert "C-DE-1003" in held_ids  # empty email
    assert "C-AT-2002" in held_ids  # invalid email


def test_hr_kpi_excludes_noncurrent():
    kpi, held = marts.hr_kpi()
    held_ids = {r["employee_id"] for r in held}
    assert {"E-3", "E-4", "E-5"} <= held_ids


def test_lineage_file_present():
    assert os.path.exists(os.path.join(REPO_ROOT, "dbt", "lineage.yaml"))
