"""Phase 5 — classification, RoPA, retention, access (requirements R5).

* the tag set is assigned to fields
* all six POL-GDPR policies are defined and mapped to a check/workflow
* RoPA validates against its schema and has the Art. 30(1) field set for
  Customer + HR
* retention flags only (never deletes)
* access checks: role + documented purpose required for personal data
* HR stays local (RoPA says local-only, HR contract localOnly=true)
* no copied statutory text (policy titles are our own wording)
"""

import os

import pytest

from dgqp import policies, validate, yaml_min
from conftest import REPO_ROOT

GOV = os.path.join(REPO_ROOT, "governance")


# --- classification tag set ------------------------------------------------

def test_tag_set_assigned_to_fields():
    assert policies.classification_for("customer.email") == ["pii.contact"]
    assert policies.classification_for("hr.employee_id") == ["pii.hr"]
    assert policies.classification_for("finance.cost_centre_id") == ["confidential.finance"]
    assert policies.classification_for("customer.customer_id") == ["master.customer"]


# --- POL-GDPR-01..06 -------------------------------------------------------

def test_all_six_policies_defined_and_mapped():
    by_id = policies.policy_by_id()
    assert set(by_id) == set(policies.POLICY_IDS)
    for pid, p in by_id.items():
        assert p["check_type"]
        assert p["on_fail"]
        assert p["article"]  # article id for traceability only


def test_minimisation_blocks_extra_fields():
    allowed = ["customer_id", "email"]
    assert policies.minimisation_ok(["customer_id"], allowed) is True
    assert policies.minimisation_ok(["customer_id", "email"], allowed) is True
    assert policies.minimisation_ok(["customer_id", "salary"], allowed) is False


# --- RoPA ------------------------------------------------------------------

def test_ropa_validates_against_schema():
    schema = validate.load_schema(os.path.join(REPO_ROOT, "schemas", "ropa.schema.json"))
    data = yaml_min.load_file(os.path.join(GOV, "ropa", "ropa.yaml"))
    validate.validate(data, schema)


def test_ropa_covers_customer_and_hr_with_full_field_set():
    activities = policies.load_ropa()
    ids = {a["activity_id"] for a in activities}
    assert {"RoPA-CUS-01", "RoPA-HR-01"} <= ids
    for a in activities:
        assert policies.ropa_entry_complete(a), a["activity_id"]
    assert policies.ropa_covers(["Customer", "HR"]) is True


def test_ropa_completeness_detects_missing_field():
    incomplete = {
        "activity_id": "X", "controller": "c", "purposes": ["p"],
        "categories_of_data_subjects": ["s"], "categories_of_personal_data": ["d"],
        "categories_of_recipients": ["r"], "retention_time_limits": "",
        "security_measures": "m",
    }
    assert policies.ropa_entry_complete(incomplete) is False


# --- retention: flag only, never delete ------------------------------------

def test_retention_flags_past_window_and_never_deletes():
    flag = policies.flag_past_retention(
        record_key="C-1", last_activity="2000-01-01",
        retention_class="customer-standard", reference_date="2026-11-15",
    )
    assert flag is not None
    assert flag.action == "flag"  # never "delete"


def test_retention_no_flag_within_window():
    flag = policies.flag_past_retention(
        record_key="C-2", last_activity="2026-01-01",
        retention_class="customer-standard", reference_date="2026-11-15",
    )
    assert flag is None


def test_retention_action_is_always_flag_in_config():
    # Defensive: the config/docs must not instruct production deletion.
    with open(os.path.join(GOV, "classification", "assignments.yaml"), encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "never performs production deletion" in text or "flag only" in text


# --- POL-GDPR-06 access ----------------------------------------------------

def test_access_requires_role_and_purpose():
    role = "Data Steward (Datenverantwortlicher, HR)"
    assert policies.access_allowed("pii.hr", role, purpose="HR admin review") is True
    assert policies.access_allowed("pii.hr", role, purpose="") is False  # no purpose
    assert policies.access_allowed("pii.hr", "Marketing", purpose="campaign") is False


def test_access_denied_for_unknown_classification():
    assert policies.access_allowed("secret.unknown", "DPO (Tarsfeld, fictional)", "x") is False


# --- HR stays local --------------------------------------------------------

def test_hr_ropa_is_local_only():
    hr = next(a for a in policies.load_ropa() if a["activity_id"] == "RoPA-HR-01")
    assert "local" in hr["categories_of_recipients"][0].lower()
    assert "local" in hr["third_country_transfers"].lower() or "none" in hr["third_country_transfers"].lower()
    contract = yaml_min.load_file(os.path.join(REPO_ROOT, "contracts", "hr.odcs.yaml"))
    assert contract["customProperties"]["localOnly"] is True


# --- no copied statutory text ----------------------------------------------

def test_policies_cite_article_ids_not_quoted_text():
    # The policy file must reference article IDs for traceability but not quote
    # long statutory passages. Heuristic: no policy "title" is a long sentence.
    for p in policies.load_policies()["policies"]:
        assert len(p["title"].split()) <= 8, p["id"]
