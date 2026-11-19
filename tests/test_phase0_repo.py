"""Phase 0 — the repo foundation files exist and the published icon diagram is
kept and referenced (requirements R8.4; design s10).
"""

import os

import pytest

from conftest import REPO_ROOT


@pytest.mark.parametrize(
    "relpath",
    [
        "Makefile",
        "pytest.ini",
        "CONTRIBUTING.md",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        "schemas/odcs-contract.schema.json",
        "schemas/label-pack.schema.json",
        "schemas/ropa.schema.json",
        "schemas/raci.schema.json",
        "schemas/run-file.schema.json",
        "src/dgqp/__init__.py",
    ],
)
def test_foundation_file_exists(relpath):
    assert os.path.exists(os.path.join(REPO_ROOT, relpath)), relpath


def test_published_icon_diagram_present():
    for name in ("architecture.png", "architecture.svg", "architecture.py"):
        assert os.path.exists(os.path.join(REPO_ROOT, "docs", "diagrams", name)), name


def test_readme_references_icon_figure():
    with open(os.path.join(REPO_ROOT, "README.md"), "r", encoding="utf-8") as fh:
        readme = fh.read()
    assert "docs/diagrams/architecture.png" in readme


def test_no_box_only_mermaid_replacement_rule_documented():
    with open(os.path.join(REPO_ROOT, "CONTRIBUTING.md"), "r", encoding="utf-8") as fh:
        contributing = fh.read()
    assert "box-only Mermaid" in contributing
