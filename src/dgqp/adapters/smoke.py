"""Hybrid smoke test (requirements R9 live path).

`python -m dgqp.cli hybrid-smoke` reads the non-HR domains that have live
adapters configured (Finance from Azure SQL, Product from Azure Blob), runs the
quality gate over the rows it got, and writes a run file under eval/results/.

Honesty and safety:
* live and mock results are reported separately; never blended
* HR is asserted untouched (no Azure adapter for HR; the guard raises otherwise)
* the run file records region but NO secret, NO server/account name, NO
  subscription id, NO SAS
* no invented numbers: figures are counts/findings measured on the rows read

With no DG_* credentials every adapter is a mock and the smoke still runs
(all-mock), which is the oss-safe default.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess

from . import config, status
from .sources import AzureBlobSource, AzureSqlSource, HrLocalOnlyError
from ..quality import gate

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RESULTS_DIR = os.path.join(REPO_ROOT, "eval", "results")


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _assert_hr_untouched() -> None:
    """HR must have no Azure source adapter; confirm the guard holds."""
    from . import sources
    try:
        sources.azure_source_for("HR")
    except HrLocalOnlyError:
        return
    raise AssertionError("HR must never have an Azure source adapter")


def run() -> dict:
    config.check_region()
    _assert_hr_untouched()

    fin = AzureSqlSource()
    prd = AzureBlobSource()

    fin_result = fin.read()
    prd_result = prd.read()

    fin_gate = gate.check_finance_rows(fin_result.rows)
    prd_gate = gate.check_product_rows(prd_result.rows)

    domains = [
        {
            "domain": "Finance",
            "adapter": "azure_sql",
            "backend": fin_result.backend,       # "live" or "mock"
            "row_count": len(fin_result.rows),
            "gate_rule": "DQ-FIN-001",
            "gate_findings": len(fin_gate.findings),
        },
        {
            "domain": "Product",
            "adapter": "azure_blob",
            "backend": prd_result.backend,
            "row_count": len(prd_result.rows),
            "gate_rule": "DQ-PRD-001",
            "gate_findings": len(prd_gate.findings),
        },
    ]
    return {
        "profile": config.profile(),
        "region": config.ALLOWED_REGION,
        "hr_to_azure": False,
        "adapters": [
            {"name": a["name"], "live": a["live"]}
            for a in status.summary()["adapters"]
        ],
        "domains": domains,
    }


def write_run(summary: dict) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    now = _now()
    live_domains = [d for d in summary["domains"] if d["backend"] == "live"]
    mock_domains = [d for d in summary["domains"] if d["backend"] == "mock"]
    payload = {
        "kind": "hybrid",
        "generated_at": now,
        "git_sha": _git_sha(),
        "profile": summary["profile"],
        "metrics": {
            "region": summary["region"],
            "hr_to_azure": summary["hr_to_azure"],
            "live": live_domains,
            "mock": mock_domains,
        },
        "notes": ("Hybrid smoke. Live and mock domains are listed separately. "
                  "No secret, server/account name or subscription id is recorded. "
                  "No live numbers are invented; figures are measured on the rows "
                  "actually read."),
    }
    path = os.path.join(RESULTS_DIR, f"hybrid-{now.replace(':', '')}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path
