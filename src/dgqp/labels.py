"""AI label export — AI-FIT-01 (requirements R7).

Computes a versioned label pack for the sibling AI platform. An asset/field is
``fit_for_ai`` only when ALL of these hold (docs/RULES-AND-POLICIES.md AI-FIT-01):

* it has a named Data Owner and Data Steward (GOV-RACI-01)
* it is classified
* the relevant quality-gate rules have passed
* where the data are personal, POL-GDPR-01, 02, 04 and 06 have been applied
* lineage to the source is recorded

Otherwise the label is ``not_fit_for_ai``. This repo PUBLISHES the label; it
does not decide allow/ask/deny (that is the sibling PEP). It does not store
prompt bodies and does not edit sibling repos. Standard-library only.
"""

from __future__ import annotations

import datetime as _dt
import json
import os

from . import governance, lineage, policies
from .quality import gate, registry

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_DIR = os.path.join(REPO_ROOT, "labels", "export")

PACK_VERSION = "1.0.0"
POLICY_VERSION = "1.0.0"

PERSONAL_TAGS = ("pii.contact", "pii.hr")
# POL-GDPR policies that must be applied where data are personal (AI-FIT-01).
REQUIRED_PERSONAL_POLICIES = ("POL-GDPR-01", "POL-GDPR-02", "POL-GDPR-04", "POL-GDPR-06")


def _is_personal(classification: list[str]) -> bool:
    return any(tag in PERSONAL_TAGS for tag in classification)


def _rules_passed(rule_ids: list[str], gate_result: gate.GateResult) -> bool:
    """True when none of the element's quality rules produced a finding."""
    for rid in rule_ids:
        if gate_result.for_rule(rid):
            return False
    return True


def _personal_policies_applied(classification: list[str]) -> bool:
    """For personal data, the required POL-GDPR policies must exist and the RoPA
    must cover the domain. Non-personal elements skip this condition.
    """
    if not _is_personal(classification):
        return True
    defined = set(policies.policy_by_id())
    if not set(REQUIRED_PERSONAL_POLICIES) <= defined:
        return False
    domains = []
    if "pii.contact" in classification:
        domains.append("Customer")
    if "pii.hr" in classification:
        domains.append("HR")
    return policies.ropa_covers(domains)


def compute_labels(gate_result: gate.GateResult | None = None) -> list[dict]:
    """Compute one label record per catalogued critical element, plus one per
    derived KPI aggregate.

    A critical *element* reflects the as-is source: on the dirty extracts its
    quality rule fails, so it is ``not_fit_for_ai`` (honest for the as-is view).
    A derived *KPI aggregate* is built only from gate-passing rows (the Phase 2
    marts hold out failures), so a non-PII aggregate with recorded lineage is
    ``fit_for_ai`` — the "already-approved, non-PII KPI aggregate" in DESIGN.md
    s9 step 5.
    """
    result = gate_result if gate_result is not None else gate.run_gate()
    lineage_ok = lineage.coverage_complete()
    lineage_by_domain = lineage.by_domain()
    lineage_domains = set(lineage_by_domain)

    labels: list[dict] = []
    for el in governance.catalog_elements():
        classification = list(el.get("classification", []))
        has_owner = bool(el.get("owner") and el.get("steward"))
        classified = bool(classification)
        rules_ok = _rules_passed(el.get("quality_rules", []), result)
        policies_ok = _personal_policies_applied(classification)
        element_lineage = lineage_ok and el.get("domain") in lineage_domains

        fit = all([has_owner, classified, rules_ok, policies_ok, element_lineage])
        tag = "fit_for_ai" if fit else "not_fit_for_ai"

        labels.append(
            {
                "asset_id": el.get("contract_id"),
                "field": el["element_id"],
                "classification": classification + [tag],
                "owner": el.get("owner"),
                "steward": el.get("steward"),
                "fit_for_ai": fit,
                "policy_version": POLICY_VERSION,
            }
        )

    labels.extend(_kpi_aggregate_labels(lineage_by_domain))
    return labels


# Non-PII KPI aggregates eligible to be fit_for_ai once their lineage is
# recorded. Personal-data domains (HR) are NOT exposed as a fit aggregate here;
# the HR aggregate stays not_fit_for_ai.
_NON_PII_AGGREGATES = {
    "Customer": ("customer.kpi.reachability", []),   # a count, no contact PII
    "Product": ("product.kpi.completeness", []),
    "Finance": ("finance.kpi.valid_spend", ["confidential.finance"]),
}


def _kpi_aggregate_labels(lineage_by_domain: dict) -> list[dict]:
    raci = {r["element_id"]: r for r in governance.load_raci()}
    domain_owner = {}
    for row in raci.values():
        domain_owner.setdefault(row["domain"], (row["owner"], row["steward"]))

    out: list[dict] = []
    for domain, (field, classification) in _NON_PII_AGGREGATES.items():
        ds = lineage_by_domain.get(domain)
        owner, steward = domain_owner.get(domain, (None, None))
        # confidential.finance aggregate is not personal but is confidential, so
        # it is fit_for_ai for labelling purposes yet the gateway will "ask".
        fit = bool(ds and owner and steward)
        tag = "fit_for_ai" if fit else "not_fit_for_ai"
        out.append(
            {
                "asset_id": ds.get("mart") if ds else None,
                "field": field,
                "classification": classification + [tag],
                "owner": owner,
                "steward": steward,
                "fit_for_ai": fit,
                "policy_version": POLICY_VERSION,
            }
        )
    return out


def build_pack(gate_result: gate.GateResult | None = None,
               generated_at: str | None = None) -> dict:
    now = generated_at or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "pack_version": PACK_VERSION,
        "generated_at": now,
        "labels": compute_labels(gate_result),
    }


def write_pack(path: str | None = None, generated_at: str | None = None) -> str:
    os.makedirs(EXPORT_DIR, exist_ok=True)
    target = path or os.path.join(EXPORT_DIR, "label-pack.json")
    pack = build_pack(generated_at=generated_at or "1970-01-01T00:00:00Z")
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(pack, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return target


if __name__ == "__main__":
    print(write_pack())
