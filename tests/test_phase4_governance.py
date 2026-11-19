"""Phase 4 — catalog, glossary, ownership/RACI (requirements R4).

* every critical element resolves owner, steward, definition, classification,
  contract link and quality-rule link (GOV-RACI-01 + GOV-META-01)
* glossary terms carry a German alias (EN + DE)
* the steward label is bilingual and is not the GDPR controller
* the recorded catalog fixture matches the live glossary+RACI join, so CI needs
  no live OpenMetadata
* RACI validates against its schema; the ingestion config lists the tag set
"""

import os

import pytest

from dgqp import governance, validate, yaml_min
from conftest import REPO_ROOT

GOV = os.path.join(REPO_ROOT, "governance")


def test_every_critical_element_is_complete():
    elements = governance.catalog_elements()
    assert len(elements) == 5
    for el in elements:
        assert governance.element_complete(el), el["element_id"]


@pytest.mark.parametrize("domain", list(governance.DOMAINS))
def test_each_domain_has_at_least_one_element(domain):
    domains = {el["domain"] for el in governance.catalog_elements()}
    assert domain in domains


def test_glossary_terms_have_german_alias():
    for term in governance.load_glossary():
        assert term.get("term_en")
        assert term.get("term_de"), f"{term['element_id']} missing German alias"


def test_steward_label_bilingual_and_not_controller():
    for row in governance.load_raci():
        assert "Datenverantwortlicher" in row["steward"]
        # The steward must not be labelled the GDPR controller (Verantwortlicher
        # without the Daten- prefix / "controller").
        assert "controller" not in row["steward"].lower()
    # The catalog's role note explains the distinction.
    with open(os.path.join(REPO_ROOT, "docs", "RULES-AND-POLICIES.md"), encoding="utf-8") as fh:
        catalog = fh.read()
    assert "Datenverantwortlicher" in catalog


def test_dpo_consulted_on_personal_data_elements():
    by_id = {el["element_id"]: el for el in governance.catalog_elements()}
    assert by_id["customer.email"]["dpo_consulted"] is True
    assert by_id["hr.employee_id"]["dpo_consulted"] is True
    assert by_id["product.product_id"]["dpo_consulted"] is False


def test_recorded_fixture_matches_live_join():
    # CI validates the fixture; it must equal the current glossary+RACI join so
    # the pipeline needs no live OpenMetadata (R4.1).
    built = governance.build_catalog_fixture()
    recorded = governance.load_catalog_fixture()
    assert built == recorded, "run `python -m dgqp.governance` to refresh the fixture"


def test_raci_validates_against_schema():
    schema = validate.load_schema(os.path.join(REPO_ROOT, "schemas", "raci.schema.json"))
    data = yaml_min.load_file(os.path.join(GOV, "raci", "register.yaml"))
    validate.validate(data, schema)


def test_ingestion_config_lists_tag_set():
    cfg = yaml_min.load_file(os.path.join(GOV, "catalog", "openmetadata-ingestion.yaml"))
    tags = set(cfg["classification"]["tags"])
    for required in ("pii.contact", "pii.hr", "confidential.finance",
                     "master.customer", "fit_for_ai", "not_fit_for_ai"):
        assert required in tags


def test_element_incomplete_when_missing_a_link():
    bad = {
        "element_id": "x", "definition": "d", "technical_name": "t",
        "contract_id": "c", "owner": "o", "steward": "s",
        "classification": [], "quality_rules": ["R"],
    }
    assert governance.element_complete(bad) is False  # no classification


def test_mdm_doc_present_and_recommends_buy():
    path = os.path.join(GOV, "mdm", "GOV-MDM-01.md")
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert "SAP MDG" in text
    assert "customer_id" in text and "product_id" in text
