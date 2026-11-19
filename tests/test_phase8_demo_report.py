"""Phase 8 — demo, report, eval persistence, README (requirements R8).

* the demo runs end to end on the stdlib path (no Docker) and well under budget
* a committed run file exists with kind, UTC timestamp, git_sha, profile, metrics
* the scorecard reads numbers ONLY from committed run files
* make report builds a PDF that embeds the published icon PNG (not Mermaid)
* make report fails closed on a missing section or an unsourced results number
* the README is a ~3-minute skim and references the icon figure
"""

import glob
import json
import os

import pytest

from dgqp import demo, pdf, report, scorecard, validate
from conftest import REPO_ROOT

RESULTS = os.path.join(REPO_ROOT, "eval", "results")


# --- demo ------------------------------------------------------------------

def test_demo_runs_and_is_fast():
    summary = demo.run(write_run=False)
    assert summary["gate_findings"] >= 6
    assert summary["ai_bridge"]["hr"] == "deny"
    assert summary["ai_bridge"]["product_kpi"] == "allow"
    # stdlib path must be far under the 15-minute (900s) budget
    assert summary["duration_seconds"] < 60


def test_demo_write_run_is_schema_valid(tmp_path):
    summary = demo.run(write_run=False)
    payload = {
        "kind": "scorecard",
        "generated_at": "2026-11-15T11:00:00Z",
        "git_sha": "deadbee",
        "profile": "oss",
        "metrics": summary["scorecard"],
    }
    schema = validate.load_schema(os.path.join(REPO_ROOT, "schemas", "run-file.schema.json"))
    validate.validate(payload, schema)


# --- committed run files ---------------------------------------------------

def test_a_committed_run_file_exists_and_validates():
    files = glob.glob(os.path.join(RESULTS, "*.json"))
    assert files, "expected at least one committed run file under eval/results/"
    schema = validate.load_schema(os.path.join(REPO_ROOT, "schemas", "run-file.schema.json"))
    for path in files:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        validate.validate(data, schema)
        assert data["git_sha"]
        assert data["generated_at"].endswith("Z")


def test_scorecard_numbers_come_from_committed_run_file():
    run = scorecard.latest_scorecard_run()
    assert run is not None
    rendered = scorecard.render_scorecard()
    # a measured dimension value from the run file appears with its source
    assert run["git_sha"] in rendered


def test_scorecard_placeholder_without_run_file(tmp_path):
    rendered = scorecard.render_scorecard(results_dir=str(tmp_path))
    assert "TO BE MEASURED" in rendered


# --- report (PDF + icon figure, fail-closed) -------------------------------

def test_report_builds_pdf_with_embedded_png():
    data = report.build_pdf()
    assert data.startswith(b"%PDF-1.4")
    assert data.rstrip().endswith(b"%%EOF")
    assert b"/Subtype /Image" in data and b"/FlateDecode" in data


def test_report_embeds_published_icon_png_not_mermaid():
    # The figure embedded is the published PNG decoded to RGB; confirm it decodes.
    with open(report.FIGURE, "rb") as fh:
        w, h, rgb = pdf.decode_png_rgb(fh.read())
    assert w > 0 and h > 0 and len(rgb) == w * h * 3


def test_report_fails_closed_on_missing_section(monkeypatch):
    broken = "## 1. Client brief\nonly one section\n"
    monkeypatch.setattr(report, "_read_case_study", lambda: broken)
    with pytest.raises(report.ReportError):
        report.build_pdf()


def test_report_fails_closed_on_unsourced_number(monkeypatch, tmp_path):
    # Results row with a number but no committed run file -> fail closed.
    md = (
        "## 1. Client brief\nx\n## 2. Problem diagnosis\nx\n"
        "## 3. Options and decision\nx\n## 4. Solution\nx\n"
        "## 5. Results\n| Result | Figure | Source |\n|---|---|---|\n"
        "| Quality completeness | 0.95 | — |\n"
        "## 6. Roadmap and recommendation\nx\n"
    )
    monkeypatch.setattr(report, "_read_case_study", lambda: md)
    monkeypatch.setattr(report.scorecard, "latest_scorecard_run",
                        lambda results_dir=None: None)
    with pytest.raises(report.ReportError):
        report.build_pdf()


def test_report_allows_placeholder_results(monkeypatch):
    md = (
        "## 1. Client brief\nx\n## 2. Problem diagnosis\nx\n"
        "## 3. Options and decision\nx\n## 4. Solution\nx\n"
        "## 5. Results\n| Result | Figure | Source |\n|---|---|---|\n"
        "| Quality completeness | TO BE MEASURED | — |\n"
        "## 6. Roadmap and recommendation\nx\n"
    )
    monkeypatch.setattr(report, "_read_case_study", lambda: md)
    monkeypatch.setattr(report.scorecard, "latest_scorecard_run",
                        lambda results_dir=None: None)
    data = report.build_pdf()  # placeholders are the honest state, not a failure
    assert data.startswith(b"%PDF-1.4")


# --- README skim -----------------------------------------------------------

def test_readme_is_skimmable_and_references_icon_figure():
    with open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8") as fh:
        readme = fh.read()
    assert "docs/diagrams/architecture.png" in readme
    for heading in ("## Problem", "## How to run", "## Results", "## Limitations"):
        assert heading in readme, heading
    # ~3-minute skim: keep it short.
    assert len(readme.splitlines()) < 120


def test_readme_figures_match_committed_run_file():
    # No invented metrics: every numeric KPI figure in the README Results table
    # must equal a value in the committed run file (guards against drift).
    run = scorecard.latest_scorecard_run()
    assert run is not None, "a committed run file must back the README figures"
    metrics = run["metrics"]
    with open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8") as fh:
        readme = fh.read()
    import re
    expected = {
        "Completeness": metrics["completeness"],
        "Uniqueness": metrics["uniqueness"],
        "Consistency": metrics["consistency"],
        "Currentness": metrics["currentness"],
        "Cross-domain key match": metrics["cross_domain_key_match"],
    }
    for label, value in expected.items():
        row = next((ln for ln in readme.splitlines()
                    if ln.strip().startswith(f"| {label} ")), None)
        assert row is not None, f"README missing results row for {label}"
        shown = re.findall(r"\d+\.\d+", row)
        assert shown, f"no figure in README row for {label}"
        assert abs(float(shown[0]) - float(value)) < 1e-9, \
            f"README {label}={shown[0]} != run file {value}"
