"""GDPR-mapped policy checks (POL-GDPR-01..06, requirements R5).

Loads the policy definitions, classification assignments and the access policy,
and provides the executable checks:

* minimisation (POL-GDPR-01): an export carries only contract-necessary fields
* retention (POL-GDPR-03): flag rows past their retention date — never delete
* RoPA completeness (POL-GDPR-04): a personal-data activity has a RoPA entry
* access (POL-GDPR-06): a role may read a classification only for a documented
  purpose

Mappings are illustrative, not a conformity claim. Standard-library only.
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass

from . import yaml_min

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POLICIES = os.path.join(REPO_ROOT, "governance", "policies", "gdpr-policies.yaml")
CLASSIFICATION = os.path.join(REPO_ROOT, "governance", "classification", "assignments.yaml")
ROPA = os.path.join(REPO_ROOT, "governance", "ropa", "ropa.yaml")

POLICY_IDS = ("POL-GDPR-01", "POL-GDPR-02", "POL-GDPR-03",
              "POL-GDPR-04", "POL-GDPR-05", "POL-GDPR-06")


def load_policies() -> dict:
    return yaml_min.load_file(POLICIES)


def policy_by_id() -> dict[str, dict]:
    return {p["id"]: p for p in load_policies()["policies"]}


def load_classification() -> dict:
    return yaml_min.load_file(CLASSIFICATION)


def classification_for(field: str) -> list[str]:
    for row in load_classification()["fields"]:
        if row["field"] == field:
            return list(row.get("classification", []))
    return []


def load_ropa() -> list[dict]:
    return yaml_min.load_file(ROPA)["activities"]


# --- POL-GDPR-01 minimisation ---------------------------------------------

def minimisation_ok(export_fields: list[str], allowed_fields: list[str]) -> bool:
    """True when the export carries only fields the contract allows."""
    return set(export_fields) <= set(allowed_fields)


# --- POL-GDPR-03 retention (flag only, never delete) ----------------------

@dataclass(frozen=True)
class RetentionFlag:
    record_key: str
    retention_class: str
    action: str = "flag"  # never "delete" — the lab does not delete in prod


def retention_window_days(retention_class: str) -> int | None:
    for row in load_classification().get("retention_classes", []):
        if row["name"] == retention_class:
            return int(row["window_days"])
    return None


def flag_past_retention(record_key: str, last_activity: str, retention_class: str,
                        reference_date: str) -> RetentionFlag | None:
    """Return a flag (action='flag') when a row is past retention; else None.

    Never deletes. The action is always 'flag' (POL-GDPR-03).
    """
    window = retention_window_days(retention_class)
    if window is None:
        return None
    try:
        last = _dt.date.fromisoformat(last_activity)
        ref = _dt.date.fromisoformat(reference_date)
    except ValueError:
        return None
    if (ref - last).days > window:
        return RetentionFlag(record_key=record_key, retention_class=retention_class)
    return None


# --- POL-GDPR-04 RoPA completeness ----------------------------------------

_ROPA_REQUIRED = (
    "controller", "purposes", "categories_of_data_subjects",
    "categories_of_personal_data", "categories_of_recipients",
    "retention_time_limits", "security_measures",
)


def ropa_entry_complete(activity: dict) -> bool:
    for field in _ROPA_REQUIRED:
        value = activity.get(field)
        if not value:
            return False
    return True


def ropa_covers(personal_data_domains: list[str]) -> bool:
    """True when the RoPA has a complete entry touching each named domain's data."""
    activities = load_ropa()
    if not all(ropa_entry_complete(a) for a in activities):
        return False
    blob = " ".join(
        str(a.get("categories_of_personal_data", "")) + " " + str(a.get("purposes", ""))
        for a in activities
    ).lower()
    tokens = {"Customer": "pii.contact", "HR": "pii.hr"}
    for domain in personal_data_domains:
        token = tokens.get(domain, domain.lower())
        if token not in blob:
            return False
    return True


# --- POL-GDPR-06 access ----------------------------------------------------

def access_rule_for(classification: str) -> dict | None:
    for rule in load_policies().get("access_policy", []):
        if rule["classification"] == classification:
            return rule
    return None


def access_allowed(classification: str, role: str, purpose: str | None) -> bool:
    """True when the role may read the classification for a documented purpose."""
    rule = access_rule_for(classification)
    if rule is None:
        return False
    if role not in rule["allowed_roles"]:
        return False
    if rule.get("purpose_required") and not (purpose or "").strip():
        return False
    return True
