"""Phase 3 — quality gate + scorecard (requirements R3).

* one pass/fail test per DQ-* rule, asserting the exact severity and on-fail
  action from the catalog
* the fail-closed executor opens a steward issue for every failure (no silent
  skip) and withholds fit_for_ai where required
* the scorecard shows placeholders until a committed run file exists
* the declarative GE/dbt mirror matches the registry
"""

import os

import pytest

from dgqp import scorecard, synthdata, yaml_min
from dgqp.quality import gate, registry, rules
from conftest import REPO_ROOT


@pytest.fixture(scope="module", autouse=True)
def _data():
    synthdata.generate()


# --- registry transcription: severities and actions match the catalog ----

EXPECTED = {
    "DQ-CUS-001": ("high", {"quarantine", "open_issue", "no_export", "not_fit_for_ai"}),
    "DQ-CUS-002": ("critical", {"block_product", "open_issue"}),
    "DQ-CUS-003": ("high", {"quarantine", "open_issue", "no_export"}),
    "DQ-PRD-001": ("high", {"quarantine", "open_issue"}),
    "DQ-FIN-001": ("critical", {"block_mart_row", "open_issue", "no_export"}),
    "DQ-HR-001": ("high", {"quarantine", "open_issue", "not_fit_for_ai", "no_export"}),
}


def test_registry_covers_all_six_rules():
    assert set(registry.all_rule_ids()) == set(EXPECTED)


@pytest.mark.parametrize("rule_id", sorted(EXPECTED))
def test_registry_severity_and_actions(rule_id):
    severity, actions = EXPECTED[rule_id]
    rule = registry.get(rule_id)
    assert rule.severity == severity
    assert set(rule.actions) == actions


# --- per-rule pass and fail -----------------------------------------------

def test_dq_cus_001_pass_and_fail():
    assert rules.customer_email_valid({"email": "a@b.example"}) is True
    assert rules.customer_email_valid({"email": ""}) is False
    assert rules.customer_email_valid({"email": "nope"}) is False


def test_dq_cus_002_pass_and_fail():
    rows = [
        {"customer_id": "X", "company": "DE01"},
        {"customer_id": "X", "company": "AT01"},
        {"customer_id": "Y", "company": "DE01"},
    ]
    dups = rules.customer_ids_unique(rows)
    assert dups == {"X"}
    assert rules.customer_id_row_ok({"customer_id": "Y"}, dups) is True
    assert rules.customer_id_row_ok({"customer_id": "X"}, dups) is False
    assert rules.customer_id_row_ok({"customer_id": ""}, dups) is False


def test_dq_cus_003_pass_fail_and_allowed_empty():
    assert rules.customer_vat_valid({"vat_id": "DE111111111"}) is True
    assert rules.customer_vat_valid({"vat_id": "ATU33333333"}) is True
    assert rules.customer_vat_valid({"vat_id": "DE12AB"}) is False
    assert rules.customer_vat_valid({"vat_id": ""}) is True  # allowed empty


def test_dq_prd_001_pass_and_fail():
    ok = {"product_id": "P", "name": "n", "status": "active", "unit_of_measure": "EA"}
    assert rules.product_mandatory_present(ok) is True
    bad = dict(ok, unit_of_measure="")
    assert rules.product_mandatory_present(bad) is False


def test_dq_fin_001_reference_and_reconciliation():
    ref = [
        {"cost_centre_id": "CC-1", "company": "DE01", "active": "true"},
        {"cost_centre_id": "CC-2", "company": "DE01", "active": "false"},
    ]
    assert rules.finance_cost_centre_valid({"cost_centre_id": "CC-1", "company": "DE01"}, ref) is True
    assert rules.finance_cost_centre_valid({"cost_centre_id": "CC-2", "company": "DE01"}, ref) is False
    assert rules.finance_cost_centre_valid({"cost_centre_id": "CC-9", "company": "DE01"}, ref) is False
    postings = [{"company": "DE01", "amount": "100.00"}, {"company": "DE01", "amount": "200.00"}]
    totals_ok = [{"company": "DE01", "reported_total": "300.00"}]
    totals_bad = [{"company": "DE01", "reported_total": "350.00"}]
    assert rules.finance_reconciles("DE01", postings, totals_ok) is True
    assert rules.finance_reconciles("DE01", postings, totals_bad) is False


def test_dq_hr_001_pass_and_fail():
    ok = {"status": "active", "effective_from": "2022-01-01",
          "effective_to": "", "last_verified_on": "2026-10-01"}
    assert rules.hr_record_current(ok) is True
    stale = dict(ok, last_verified_on="2024-01-01")
    assert rules.hr_record_current(stale) is False
    leaver = {"status": "leaver", "effective_from": "2020-01-01",
              "effective_to": "", "last_verified_on": "2026-10-01"}
    assert rules.hr_record_current(leaver) is False
    no_status = dict(ok, status="")
    assert rules.hr_record_current(no_status) is False


# --- fail-closed executor -------------------------------------------------

def test_gate_finds_every_rule_and_opens_issues():
    result = gate.run_gate()
    found_rules = {f.rule_id for f in result.findings}
    assert found_rules == set(EXPECTED), "every DQ-* rule must fire on the dirty set"
    # No silent skip: every finding carries a steward issue id and actions.
    for f in result.findings:
        assert f.issue_id.startswith("ISS-")
        assert "open_issue" in f.actions
        assert f.severity in registry.SEVERITIES


def test_gate_withholds_fit_for_ai_for_cus001_and_hr001():
    result = gate.run_gate()
    for rid in ("DQ-CUS-001", "DQ-HR-001"):
        findings = result.for_rule(rid)
        assert findings
        for f in findings:
            assert "not_fit_for_ai" in f.actions


def test_gate_blocks_customer_product_on_cus002():
    result = gate.run_gate()
    assert "Customer" in result.blocked_products


def test_gate_is_not_a_silent_skip():
    # The dirty-by-design set must produce findings; a clean pass here would
    # mean the gate skipped rules.
    result = gate.run_gate()
    assert not result.passed
    assert len(result.findings) >= len(EXPECTED)


# --- scorecard placeholder behaviour --------------------------------------

def test_scorecard_shows_placeholders_without_run_file(tmp_path):
    rendered = scorecard.render_scorecard(results_dir=str(tmp_path))
    assert "TO BE MEASURED" in rendered
    assert "completeness" in rendered
    # no stray numbers in a placeholder scorecard
    assert "0." not in rendered


def test_scorecard_reads_committed_run_file(tmp_path):
    run = tmp_path / "scorecard-x.json"
    run.write_text(
        '{"kind":"scorecard","generated_at":"2026-11-15T10:00:00Z",'
        '"git_sha":"abc1234","profile":"oss",'
        '"metrics":{"completeness":0.8,"uniqueness":0.9}}'
    )
    rendered = scorecard.render_scorecard(results_dir=str(tmp_path))
    assert "0.8" in rendered
    assert "abc1234" in rendered


# --- declarative mirror matches the registry ------------------------------

def test_expectations_mirror_matches_registry():
    path = os.path.join(REPO_ROOT, "quality", "expectations.yaml")
    data = yaml_min.load_file(path)
    by_id = {s["rule_id"]: s for s in data["suites"]}
    assert set(by_id) == set(registry.all_rule_ids())
    for rid, suite in by_id.items():
        rule = registry.get(rid)
        assert suite["severity"] == rule.severity
        assert set(suite["actions"]) == set(rule.actions)


def test_vat_pattern_documented_as_contract_parameter():
    # R3.5: the VAT per-country pattern is a contract parameter, not official.
    data = yaml_min.load_file(os.path.join(REPO_ROOT, "contracts", "customer.odcs.yaml"))
    note = data["customProperties"]["vatPatternNote"]
    assert "NOT official" in note
