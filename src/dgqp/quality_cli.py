"""`make quality` entry point: run the fail-closed quality gate and report.

By default this prints the findings and exits non-zero if the gate found any
failure (fail closed). It does NOT write a measurement unless asked with
``--write-run``, and even then the scorecard only shows numbers once that run
file is committed (no invented metrics; requirements R3.2, R3.4, R8.5).

Usage::

    python -m dgqp.quality_cli            # run gate, print findings, fail closed
    python -m dgqp.quality_cli --write-run  # also persist a scorecard run file
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys

from . import synthdata
from .quality import gate, registry

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(REPO_ROOT, "eval", "results")


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        )
        return out.strip()
    except Exception:
        return "unknown"


def _scorecard_metrics(result: gate.GateResult) -> dict:
    """Compute dimension pass rates from committed synthetic data + the gate."""
    # Completeness/uniqueness/consistency/currentness as the share of evaluated
    # (rule, record) checks that passed for the rules carrying that dimension.
    by_dim: dict[str, list[int]] = {}
    fails_by_rule: dict[str, int] = {}
    for f in result.findings:
        fails_by_rule[f.rule_id] = fails_by_rule.get(f.rule_id, 0) + 1
    # Rough per-dimension denominator: number of rows in the domain of each rule.
    row_counts = {
        "Customer": len(synthdata.customer_rows()),
        "Product": len(synthdata.product_rows()),
        "Finance": len(synthdata.finance_rows()),
        "HR": len(synthdata.hr_rows()),
    }
    for rid, rule in registry.REGISTRY.items():
        denom = row_counts[rule.domain]
        passed = max(denom - fails_by_rule.get(rid, 0), 0)
        for dim in rule.dimensions:
            by_dim.setdefault(dim, [0, 0])
            by_dim[dim][0] += passed
            by_dim[dim][1] += denom
    metrics = {}
    for dim, (ok, total) in by_dim.items():
        metrics[dim] = round(ok / total, 3) if total else None
    return metrics


def _write_run(result: gate.GateResult) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "kind": "scorecard",
        "generated_at": now,
        "git_sha": _git_sha(),
        "profile": "oss",
        "metrics": _scorecard_metrics(result),
        "notes": ("Measured from the committed synthetic extracts by the "
                  "fail-closed quality gate. Dirty-by-design data, so rates are "
                  "below 1.0 on purpose."),
    }
    path = os.path.join(RESULTS_DIR, f"scorecard-{now.replace(':', '')}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    synthdata.generate()
    result = gate.run_gate()

    print(f"Quality gate: {result.checked} checks, {len(result.findings)} findings")
    for f in sorted(result.findings, key=lambda x: (x.rule_id, x.record_key)):
        print(f"  FAIL {f.rule_id} [{f.severity}] {f.record_key}: {f.message} "
              f"-> issue {f.issue_id} actions={','.join(f.actions)}")

    if "--write-run" in argv:
        path = _write_run(result)
        print(f"\nWrote run file: {os.path.relpath(path, REPO_ROOT)}")
        print("Commit it for its numbers to appear in the scorecard.")

    # Fail closed: a dirty synthetic set is expected to have findings. The gate
    # exit code signals "findings present" so a CI gate job could act on it; the
    # test suite asserts the specific expected findings.
    return 1 if result.findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
