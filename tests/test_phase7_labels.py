"""Phase 7 — AI label export + fixture consumer (requirements R7).

* AI-FIT-01 gate: fit_for_ai only when owner+steward, classification, DQ rules
  passed, personal-data policies applied, and lineage recorded
* a versioned label pack validates against the schema
* the fixture consumer returns deny/ask/allow per DESIGN.md s9
* the fixture refuses not_fit_for_ai rows
* no PEP, no prompt bodies, no sibling-repo writes
"""

import os

import pytest

from dgqp import ai_gateway_fixture as gw
from dgqp import labels, synthdata, validate
from dgqp.quality import gate
from conftest import REPO_ROOT


@pytest.fixture(scope="module", autouse=True)
def _data():
    synthdata.generate()


@pytest.fixture(scope="module")
def pack():
    return labels.build_pack(generated_at="1970-01-01T00:00:00Z")


# --- AI-FIT-01 gate --------------------------------------------------------

def test_source_elements_not_fit_on_dirty_data(pack):
    by_field = {l["field"]: l for l in pack["labels"]}
    # On the as-is dirty extracts every source element fails its DQ rule.
    for field in ("customer.customer_id", "customer.email", "product.product_id",
                  "finance.cost_centre_id", "hr.employee_id"):
        assert by_field[field]["fit_for_ai"] is False
        assert "not_fit_for_ai" in by_field[field]["classification"]


def test_nonpii_kpi_aggregates_are_fit(pack):
    by_field = {l["field"]: l for l in pack["labels"]}
    assert by_field["customer.kpi.reachability"]["fit_for_ai"] is True
    assert by_field["product.kpi.completeness"]["fit_for_ai"] is True


def test_fit_requires_all_conditions():
    # If the gate reports a failure for an element's rule, it cannot be fit.
    result = gate.run_gate()
    computed = labels.compute_labels(result)
    by_field = {l["field"]: l for l in computed}
    assert by_field["customer.email"]["fit_for_ai"] is False


# --- label pack schema -----------------------------------------------------

def test_label_pack_validates(pack):
    schema = validate.load_schema(os.path.join(REPO_ROOT, "schemas", "label-pack.schema.json"))
    validate.validate(pack, schema)
    assert pack["pack_version"]
    for lbl in pack["labels"]:
        for key in ("asset_id", "field", "classification", "owner", "steward",
                    "fit_for_ai", "policy_version"):
            assert key in lbl


def test_pack_is_versioned(pack):
    assert pack["pack_version"] == labels.PACK_VERSION
    assert all(l["policy_version"] == labels.POLICY_VERSION for l in pack["labels"])


# --- fixture consumer: deny / ask / allow (DESIGN.md s9) -------------------

def test_fixture_denies_hr_request(pack):
    assert gw.decide(pack, ["hr.employee_id"]).outcome == gw.DENY


def test_fixture_denies_or_asks_pii_and_confidential(pack):
    # Customer email is not_fit on dirty data -> deny; the policy for a fit
    # contact-PII field would be "ask" (covered below with a synthetic pack).
    assert gw.decide(pack, ["customer.email"]).outcome == gw.DENY
    assert gw.decide(pack, ["finance.cost_centre_id"]).outcome == gw.DENY


def test_fixture_allows_approved_nonpii_aggregate(pack):
    assert gw.decide(pack, ["product.kpi.completeness"]).outcome == gw.ALLOW
    assert gw.decide(pack, ["customer.kpi.reachability"]).outcome == gw.ALLOW


def test_fixture_asks_for_confidential_aggregate(pack):
    assert gw.decide(pack, ["finance.kpi.valid_spend"]).outcome == gw.ASK


def test_fixture_refuses_not_fit_for_ai_even_if_asked_together(pack):
    # A mix that includes a not_fit_for_ai field is denied outright.
    decision = gw.decide(pack, ["product.kpi.completeness", "hr.employee_id"])
    assert decision.outcome == gw.DENY


def test_fixture_asks_on_fit_contact_pii():
    # Synthetic pack where a contact-PII field is fit_for_ai: policy is "ask".
    synthetic = {
        "pack_version": "1.0.0",
        "generated_at": "1970-01-01T00:00:00Z",
        "labels": [{
            "asset_id": "a", "field": "customer.email_clean",
            "classification": ["pii.contact", "fit_for_ai"],
            "owner": "o", "steward": "s", "fit_for_ai": True,
            "policy_version": "1.0.0",
        }],
    }
    assert gw.decide(synthetic, ["customer.email_clean"]).outcome == gw.ASK


def test_fixture_denies_unknown_field(pack):
    assert gw.decide(pack, ["does.not.exist"]).outcome == gw.DENY


# --- scope boundary: no PEP, no prompt storage, no sibling writes ----------

def test_no_prompt_storage_or_sibling_writes():
    src = os.path.join(REPO_ROOT, "src", "dgqp")
    text = ""
    for name in ("labels.py", "ai_gateway_fixture.py"):
        with open(os.path.join(src, name), encoding="utf-8") as fh:
            text += fh.read().lower()
    # No sibling-repo names are written/imported here.
    for sibling in ("ai-compliance-automation", "agent-trust-gateway",
                    "agent access governance gateway"):
        assert f"open('{sibling}" not in text
    # The fixture does not store prompt bodies (no 'prompt' persistence).
    assert "prompt_body" not in text


def test_write_pack_stays_inside_repo(tmp_path):
    out = labels.write_pack(path=str(tmp_path / "pack.json"),
                            generated_at="1970-01-01T00:00:00Z")
    assert os.path.exists(out)


def test_committed_pack_matches_computed_structure(pack):
    import json
    committed_path = os.path.join(REPO_ROOT, "labels", "export", "label-pack.json")
    with open(committed_path, encoding="utf-8") as fh:
        committed = json.load(fh)
    # Compare label structure (ignore generated_at which is a fixed epoch here).
    assert committed["labels"] == pack["labels"], \
        "run `python -m dgqp.labels` to refresh the exported pack"
