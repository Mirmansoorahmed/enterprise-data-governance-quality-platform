"""Phase 0 — repo foundation: the YAML subset reader, the schema validator,
and the JSON schema files all work on trivial fixtures.
"""

import json
import os

import pytest

from dgqp import validate, yaml_min
from conftest import REPO_ROOT

SCHEMAS = os.path.join(REPO_ROOT, "schemas")


# --- yaml_min -------------------------------------------------------------

def test_yaml_scalars_and_mapping():
    data = yaml_min.load(
        "a: 1\n"
        "b: 2.5\n"
        "c: true\n"
        "d: false\n"
        "e: null\n"
        "f: plain text\n"
        "g: \"quoted: colon\"\n"
    )
    assert data == {
        "a": 1, "b": 2.5, "c": True, "d": False, "e": None,
        "f": "plain text", "g": "quoted: colon",
    }


def test_yaml_nested_mapping_and_sequence():
    data = yaml_min.load(
        "root:\n"
        "  items:\n"
        "    - one\n"
        "    - two\n"
        "  child:\n"
        "    k: v\n"
    )
    assert data == {"root": {"items": ["one", "two"], "child": {"k": "v"}}}


def test_yaml_sequence_of_mappings():
    data = yaml_min.load(
        "people:\n"
        "  - name: Ada\n"
        "    role: owner\n"
        "  - name: Bo\n"
        "    role: steward\n"
    )
    assert data == {
        "people": [
            {"name": "Ada", "role": "owner"},
            {"name": "Bo", "role": "steward"},
        ]
    }


def test_yaml_flow_sequence_scalar():
    data = yaml_min.load("tags: [pii.contact, master.customer]\n")
    assert data == {"tags": ["pii.contact", "master.customer"]}


def test_yaml_flow_sequence_keeps_commas_inside_parens():
    data = yaml_min.load("roles: [Owner (A), Steward (B, C)]\n")
    assert data == {"roles": ["Owner (A)", "Steward (B, C)"]}


def test_yaml_rejects_tabs():
    with pytest.raises(yaml_min.YamlError):
        yaml_min.load("a:\n\tb: 1\n")


# --- validate -------------------------------------------------------------

def test_validate_accepts_valid():
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string", "minLength": 1}},
        "additionalProperties": False,
    }
    validate.validate({"name": "ok"}, schema)  # no raise


def test_validate_rejects_missing_required():
    schema = {"type": "object", "required": ["name"], "properties": {}}
    with pytest.raises(validate.ValidationError):
        validate.validate({}, schema)


def test_validate_enum_and_integer_vs_bool():
    schema = {"type": "integer"}
    validate.validate(3, schema)
    with pytest.raises(validate.ValidationError):
        validate.validate(True, schema)  # bool is not integer here


def test_validate_additional_properties_false():
    schema = {"type": "object", "properties": {}, "additionalProperties": False}
    with pytest.raises(validate.ValidationError):
        validate.validate({"extra": 1}, schema)


# --- schema files load and self-validate on trivial fixtures --------------

@pytest.mark.parametrize(
    "filename",
    [
        "run-file.schema.json",
        "label-pack.schema.json",
        "raci.schema.json",
        "ropa.schema.json",
        "odcs-contract.schema.json",
    ],
)
def test_schema_files_are_valid_json(filename):
    with open(os.path.join(SCHEMAS, filename), "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    assert schema["$schema"].endswith("schema#")
    assert "title" in schema


def test_run_file_schema_round_trip():
    schema = validate.load_schema(os.path.join(SCHEMAS, "run-file.schema.json"))
    good = {
        "kind": "scorecard",
        "generated_at": "2026-11-15T10:00:00Z",
        "git_sha": "abc1234",
        "profile": "oss",
        "metrics": {"completeness": 0.9},
    }
    validate.validate(good, schema)
    bad = dict(good)
    bad["generated_at"] = "not-a-timestamp"
    with pytest.raises(validate.ValidationError):
        validate.validate(bad, schema)
