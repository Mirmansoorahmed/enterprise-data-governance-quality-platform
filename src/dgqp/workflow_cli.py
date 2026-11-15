"""`python -m dgqp.workflow_cli` — demo the steward issue / cleanse loop.

Runs the fail-closed gate, picks one failed finance posting (DQ-FIN-001),
opens a steward issue, applies the documented cleanse (re-key to an active cost
centre on a working copy), re-runs the rule, and closes the issue. Prints the
issue trail and the issue-cycle counts. The committed extracts are never
mutated.

This is the business-IT interface demonstrated in DESIGN.md s9 step 4.
"""

from __future__ import annotations

import json
import os

from . import synthdata
from .quality import gate, rules
from . import workflow

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFERENCE = os.path.join(REPO_ROOT, "data", "reference")


def main() -> int:
    synthdata.generate()
    result = gate.run_gate()
    fin = result.for_rule("DQ-FIN-001")
    if not fin:
        print("No DQ-FIN-001 finding to remediate (unexpected on the dirty set).")
        return 1

    # Pick a row-scoped finding (not the reconciliation one) to cleanse.
    target = next((f for f in fin if not f.record_key.startswith("reconcile")), fin[0])
    postings = synthdata.read_csv(os.path.join(REPO_ROOT, "data", "raw", "finance", "finance_postings.csv"))
    ref = synthdata.read_csv(os.path.join(REFERENCE, "finance_company_codes.csv"))
    posting_id = target.record_key.split("#")[0]
    row = next(r for r in postings if r["posting_id"] == posting_id)

    log = workflow.WorkflowLog()
    rem = workflow.Remediation(log)
    issue = rem.remediate(
        rule_id="DQ-FIN-001",
        record_key=posting_id,
        message=target.message,
        row=row,
        decision=workflow.CLEANSE,
        note="Steward re-keyed the posting to active cost centre CC-1000 per GL.",
        cleanse=lambda r: workflow.cleanse_finance_cost_centre(r, "CC-1000"),
        check=lambda r: rules.finance_cost_centre_valid(r, ref),
    )

    print("Steward issue trail:")
    print(json.dumps(issue.to_dict(), indent=2))
    print("\nIssue-cycle counts:", json.dumps(workflow.issue_cycle_metrics(log)))
    print(f"\nRe-run of DQ-FIN-001 after cleanse passed: {issue.rerun_passed}")
    print("(The committed extract is unchanged; the cleanse ran on a working copy.)")
    return 0 if issue.rerun_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
