"""Phase 1 — synthetic data + ODCS contracts (requirements R1).

* every contract validates against the ODCS structural schema
* the YAML loader reads each contract into the expected shape
* the dirty extracts contain the seeded defect for every DQ-* rule
* HR is local-only (never an Azure source) and is not an Azure-bound domain
* the generator is deterministic
"""

import os

import pytest

from dgqp import synthdata, validate, yaml_min
from conftest import REPO_ROOT

CONTRACTS = os.path.join(REPO_ROOT, "contracts")
CONTRACT_FILES = [
    "customer.odcs.yaml",
    "product.odcs.yaml",
    "finance.odcs.yaml",
    "hr.odcs.yaml",
    "finance_costcentres.odcs.yaml",
]


@pytest.fixture(scope="module", autouse=True)
def _generate_data():
    synthdata.generate()


@pytest.fixture(scope="module")
def odcs_schema():
    return validate.load_schema(os.path.join(REPO_ROOT, "schemas", "odcs-contract.schema.json"))


@pytest.mark.parametrize("filename", CONTRACT_FILES)
def test_contract_validates(filename, odcs_schema):
    data = yaml_min.load_file(os.path.join(CONTRACTS, filename))
    validate.validate(data, odcs_schema)
    assert data["apiVersion"] == "v3.2.0"
    assert data["kind"] == "DataContract"


@pytest.mark.parametrize("filename", CONTRACT_FILES)
def test_contract_has_owner_and_steward(filename):
    data = yaml_min.load_file(os.path.join(CONTRACTS, filename))
    cp = data["customProperties"]
    assert cp["owner"]
    assert "Datenverantwortlicher" in cp["steward"]


def test_four_domains_two_companies_present():
    customers = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "customer", "customers.csv")
    )
    companies = {row["company"] for row in customers}
    assert synthdata.COMPANIES[0] in companies
    assert synthdata.COMPANIES[1] in companies


# --- seeded defects, one assertion family per DQ-* rule -------------------

def _customers():
    return synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "customer", "customers.csv")
    )


def test_defect_dq_cus_001_email():
    rows = _customers()
    assert any(r["email"] == "" for r in rows)
    assert any(r["email"] and "@" not in r["email"] for r in rows)


def test_defect_dq_cus_002_duplicate_id():
    rows = _customers()
    ids = [r["customer_id"] for r in rows]
    assert len(ids) != len(set(ids))  # a duplicate exists across companies


def test_defect_dq_cus_003_vat_pattern():
    rows = _customers()
    # The DE row with a malformed VAT is present; an allowed-empty row exists.
    assert any(r["customer_id"] == "C-DE-1004" and r["vat_id"] == "DE12AB" for r in rows)
    assert any(r["vat_id"] == "" for r in rows)


def test_defect_dq_prd_001_missing_attributes():
    rows = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "product", "products.csv")
    )
    assert any(not r["name"] or not r["unit_of_measure"] for r in rows)
    assert any(not r["status"] for r in rows)


def test_defect_dq_fin_001_reference_and_reconciliation():
    postings = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "finance", "finance_postings.csv")
    )
    ref = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "reference", "finance_company_codes.csv")
    )
    active = {(r["cost_centre_id"], r["company"]) for r in ref if r["active"] == "true"}
    known = {r["cost_centre_id"] for r in ref}
    # at least one posting references a missing cost centre
    assert any(r["cost_centre_id"] not in known for r in postings)
    # at least one posting references an inactive cost centre
    assert any(
        r["cost_centre_id"] in known and (r["cost_centre_id"], r["company"]) not in active
        for r in postings
    )
    # reconciliation defect: DE01 reported total != sum of DE01 postings
    totals = {
        r["company"]: float(r["reported_total"])
        for r in synthdata.read_csv(
            os.path.join(REPO_ROOT, "data", "raw", "finance", "finance_control_totals.csv")
        )
    }
    de_sum = sum(float(r["amount"]) for r in postings if r["company"] == "DE01")
    assert abs(totals["DE01"] - de_sum) > 0.001


def test_defect_dq_hr_001_currentness():
    rows = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "hr", "employees.csv")
    )
    assert any(r["status"] == "leaver" and not r["effective_to"] for r in rows)
    assert any(not r["status"] for r in rows)
    assert any(r["last_verified_on"] < "2025-01-01" for r in rows)  # stale


# --- HR local-only --------------------------------------------------------

def test_hr_contract_is_local_only():
    data = yaml_min.load_file(os.path.join(CONTRACTS, "hr.odcs.yaml"))
    assert data["customProperties"]["localOnly"] is True


def test_no_azure_binding_for_hr_anywhere():
    # No file in the repo may bind the HR domain to an Azure source. We assert
    # there is no hybrid source mapping yet (Phase 9), and that if/when one is
    # added it cannot include HR. For now: the HR contract declares local-only
    # and there is no sources mapping file.
    mapping = os.path.join(REPO_ROOT, "adapters", "source_mapping.yaml")
    if os.path.exists(mapping):
        data = yaml_min.load_file(mapping)
        azure = str(data).lower()
        assert "hr" not in azure or "localonly" in azure


# --- determinism ----------------------------------------------------------

def test_generator_is_deterministic():
    a = synthdata.customer_rows()
    b = synthdata.customer_rows()
    assert a == b
