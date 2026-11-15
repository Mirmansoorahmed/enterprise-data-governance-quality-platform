"""`make demo` — the DESIGN.md s9 walkthrough on the oss profile.

Runs end to end with the standard-library engine, so it works with no Docker and
no cloud account (the OpenMetadata UI is an optional local extra via
`make bootstrap`; this script uses the recorded catalog fixture instead). It is
designed to finish in well under 15 minutes after image pull; in the stdlib
path it finishes in seconds.

With ``--write-run`` it persists a committed run file under ``eval/results/``
carrying the measured scorecard, demo duration, issue-cycle counts and label
summary, each with a UTC timestamp and git SHA. The scorecard and README read
numbers ONLY from such committed files (no invented metrics).

Steps (DESIGN.md s9):
  1 brief        show the dirty extracts and the glossary
  2 catalog      glossary + ownership (recorded fixture)
  3 quality      run the rule pack, show the scorecard
  4 issue        steward cleanse loop + gate re-run
  5 ai bridge    label export + gateway fixture deny/ask/allow
  6 buy vs build pointer to the table in docs/DESIGN.md
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import time

from . import ai_gateway_fixture as gw
from . import governance, labels, scorecard, synthdata, workflow
from .quality import gate, rules

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(REPO_ROOT, "eval", "results")


def _git_sha() -> str:
    import subprocess
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scorecard_metrics(result: gate.GateResult) -> dict:
    from .quality import registry
    row_counts = {
        "Customer": len(synthdata.customer_rows()),
        "Product": len(synthdata.product_rows()),
        "Finance": len(synthdata.finance_rows()),
        "HR": len(synthdata.hr_rows()),
    }
    fails_by_rule: dict[str, int] = {}
    for f in result.findings:
        fails_by_rule[f.rule_id] = fails_by_rule.get(f.rule_id, 0) + 1
    by_dim: dict[str, list[int]] = {}
    for rid, rule in registry.REGISTRY.items():
        denom = row_counts[rule.domain]
        passed = max(denom - fails_by_rule.get(rid, 0), 0)
        for dim in rule.dimensions:
            by_dim.setdefault(dim, [0, 0])
            by_dim[dim][0] += passed
            by_dim[dim][1] += denom
    metrics = {d: round(ok / total, 3) for d, (ok, total) in by_dim.items() if total}
    # cross-domain key match: share of customer ids that are unique across both
    # companies (DQ-CUS-002 is the cross-company key check).
    customers = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "customer", "customers.csv")
    )
    dups = rules.customer_ids_unique(customers)
    total_ids = len({c["customer_id"] for c in customers})
    metrics["cross_domain_key_match"] = round((total_ids - len(dups)) / total_ids, 3)
    return metrics


def run(write_run: bool = False) -> dict:
    start = time.monotonic()
    print("=== Enterprise Data Governance & Quality Platform — demo (oss) ===\n")

    synthdata.generate()

    # 1 brief
    customers = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "raw", "customer", "customers.csv")
    )
    print(f"[1] Brief: four domains, two country companies. "
          f"{len(customers)} customer rows loaded (dirty by design).")

    # 2 catalog + ownership (recorded fixture)
    elements = governance.catalog_elements()
    print(f"[2] Catalog: {len(elements)} critical elements with EN+DE glossary, "
          f"owner and steward. e.g. "
          f"{elements[0]['term_en']} / {elements[0]['term_de']} "
          f"owned by {elements[0]['owner']}.")

    # 3 quality + scorecard
    result = gate.run_gate()
    print(f"[3] Quality gate: {result.checked} checks, {len(result.findings)} "
          f"findings (fail-closed; each opens a steward issue).")

    # 4 steward cleanse loop
    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    ref = synthdata.read_csv(
        os.path.join(REPO_ROOT, "data", "reference", "finance_company_codes.csv")
    )
    bad = {"posting_id": "F-4", "company": "DE01", "cost_centre_id": "CC-9999", "amount": "75.00"}
    issue = rem.remediate(
        "DQ-FIN-001", "F-4", "cost centre unknown", bad,
        workflow.CLEANSE, "Steward re-keyed to active CC-1000",
        lambda r: workflow.cleanse_finance_cost_centre(r, "CC-1000"),
        lambda r: rules.finance_cost_centre_valid(r, ref),
    )
    print(f"[4] Steward loop: issue {issue.issue_id} cleansed; "
          f"re-run passed={issue.rerun_passed}.")

    # 5 AI bridge
    pack = labels.build_pack(gate_result=result, generated_at="1970-01-01T00:00:00Z")
    d_hr = gw.decide(pack, ["hr.employee_id"])
    d_cus = gw.decide(pack, ["customer.email"])
    d_kpi = gw.decide(pack, ["product.kpi.completeness"])
    print(f"[5] AI bridge: HR list -> {d_hr.outcome}; customer email export -> "
          f"{d_cus.outcome}; approved product KPI aggregate -> {d_kpi.outcome}.")

    # 6 buy vs build
    print("[6] Buy vs Build: see docs/DESIGN.md s7. We keep the operating model; "
          "catalog/MDM are buy options.")

    # Hybrid posture (adapters default to mocks; absent creds -> all mocked).
    from .adapters import status as adapter_status
    hyb = adapter_status.summary()
    mocked = "all mocked" if adapter_status.all_mocked(hyb) else "some live"
    print(f"    Hybrid: profile={hyb['profile']}, region={hyb['region']}, "
          f"HR-to-Azure={hyb['hr_to_azure']}, adapters {mocked}.\n")

    duration = round(time.monotonic() - start, 3)
    print(f"Demo finished in {duration}s (budget: under 15 minutes after image pull).")

    summary = {
        "duration_seconds": duration,
        "gate_checks": result.checked,
        "gate_findings": len(result.findings),
        "issue_cycle": workflow.issue_cycle_metrics(log),
        "ai_bridge": {
            "hr": d_hr.outcome, "customer_email": d_cus.outcome,
            "product_kpi": d_kpi.outcome,
        },
        "scorecard": _scorecard_metrics(result),
    }

    if write_run:
        path = _write_run(summary)
        print(f"\nWrote run file: {os.path.relpath(path, REPO_ROOT)} "
              f"(commit it for its numbers to appear in the scorecard/README).")
    return summary


def _write_run(summary: dict) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    now = _now()
    payload = {
        "kind": "scorecard",
        "generated_at": now,
        "git_sha": _git_sha(),
        "profile": "oss",
        "metrics": {
            **summary["scorecard"],
            "demo_duration_seconds": summary["duration_seconds"],
        },
        "notes": ("Measured by `make demo --write-run` on the committed "
                  "synthetic extracts. Dirty-by-design data, so rates are below "
                  "1.0 on purpose."),
    }
    path = os.path.join(RESULTS_DIR, f"demo-{now.replace(':', '')}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the oss demo (DESIGN.md s9).")
    parser.add_argument("--write-run", action="store_true",
                        help="persist a committed run file under eval/results/")
    args = parser.parse_args()
    run(write_run=args.write_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
