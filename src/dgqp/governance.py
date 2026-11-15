"""Governance core accessor: glossary, RACI and the recorded catalog fixture.

The business glossary (``governance/glossary/glossary.yaml``) and the RACI
register (``governance/raci/register.yaml``) are the sources of truth. This
module joins them into a per-element catalog view used by the demo, the label
export (Phase 7) and the recorded fixture that CI validates instead of a live
OpenMetadata (requirements R4, design s10).

Standard-library only.
"""

from __future__ import annotations

import json
import os

from . import yaml_min

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GLOSSARY = os.path.join(REPO_ROOT, "governance", "glossary", "glossary.yaml")
RACI = os.path.join(REPO_ROOT, "governance", "raci", "register.yaml")
FIXTURE = os.path.join(REPO_ROOT, "governance", "catalog", "fixtures", "catalog.json")

DOMAINS = ("Customer", "Product", "Finance", "HR")


def load_glossary() -> list[dict]:
    return yaml_min.load_file(GLOSSARY)["terms"]


def load_raci() -> list[dict]:
    return yaml_min.load_file(RACI)["elements"]


def _raci_by_element() -> dict[str, dict]:
    return {row["element_id"]: row for row in load_raci()}


def catalog_elements() -> list[dict]:
    """Join glossary + RACI into a per-element catalog view (GOV-META-01).

    Each element resolves: definition, EN term, DE alias, technical name,
    classification, contract link, quality rule link, owner and steward.
    """
    raci = _raci_by_element()
    out: list[dict] = []
    for term in load_glossary():
        eid = term["element_id"]
        owner_row = raci.get(eid, {})
        out.append(
            {
                "element_id": eid,
                "domain": owner_row.get("domain"),
                "term_en": term.get("term_en"),
                "term_de": term.get("term_de"),
                "definition": term.get("definition"),
                "technical_name": term.get("technical_name"),
                "classification": term.get("classification", []),
                "contract_id": term.get("contract_id"),
                "quality_rules": term.get("quality_rules", []),
                "owner": owner_row.get("owner"),
                "steward": owner_row.get("steward"),
                "dpo_consulted": owner_row.get("dpo_consulted", False),
            }
        )
    return out


def element_complete(element: dict) -> bool:
    """GOV-RACI-01 + GOV-META-01: an element is 'ready for use' only when it
    resolves an owner, steward, definition, classification, contract and rule.
    """
    required = (
        "definition", "technical_name", "contract_id", "owner", "steward",
    )
    if any(not element.get(k) for k in required):
        return False
    if not element.get("classification"):
        return False
    if not element.get("quality_rules"):
        return False
    return True


def build_catalog_fixture() -> dict:
    """The recorded catalog snapshot CI validates (no live OpenMetadata)."""
    elements = catalog_elements()
    return {
        "service": "tarsfeld-dgqp",
        "glossary": "Tarsfeld Data Governance Glossary",
        "elements": elements,
    }


def write_catalog_fixture() -> str:
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as handle:
        json.dump(build_catalog_fixture(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return FIXTURE


def load_catalog_fixture() -> dict:
    with open(FIXTURE, "r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    print(write_catalog_fixture())
