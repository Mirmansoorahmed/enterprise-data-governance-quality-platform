"""Rule registry: each DQ-* ID mapped to its check, severity and on-fail action.

Severities and on-fail actions are transcribed exactly from
``docs/RULES-AND-POLICIES.md``. ``action`` is a short machine token set used by
the fail-closed executor; the human-readable summary stays in ``summary``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Severity vocabulary from the catalog s1: critical blocks the gate and any
# fit_for_ai export; high blocks the gate; medium opens an issue with a possible
# documented exception.
SEVERITIES = ("critical", "high", "medium")

# On-fail action tokens. A failure is never a silent skip.
#   quarantine      hold the row out of its data product
#   block_product   block the whole data product / campaign export
#   block_mart_row  block just this row from the mart load
#   open_issue      open a steward issue (always set on any fail)
#   no_export       do not export the row
#   not_fit_for_ai  force the not_fit_for_ai label
ACTIONS = (
    "quarantine", "block_product", "block_mart_row", "open_issue",
    "no_export", "not_fit_for_ai",
)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    domain: str
    severity: str
    actions: tuple[str, ...]
    summary: str
    scope: str = "row"  # "row" or "dataset"
    dimensions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        assert self.severity in SEVERITIES, self.severity
        for a in self.actions:
            assert a in ACTIONS, a


REGISTRY: dict[str, Rule] = {
    "DQ-CUS-001": Rule(
        rule_id="DQ-CUS-001", domain="Customer", severity="high",
        actions=("quarantine", "open_issue", "no_export", "not_fit_for_ai"),
        summary=("Fail the gate; quarantine the record; open a steward issue; "
                 "do not export the row; do not set fit_for_ai."),
        dimensions=("completeness", "consistency"),  # presence + syntactic accuracy
    ),
    "DQ-CUS-002": Rule(
        rule_id="DQ-CUS-002", domain="Customer", severity="critical",
        actions=("block_product", "open_issue"),
        summary=("Fail the gate; block the customer data product and any "
                 "campaign export; open a steward issue to resolve or merge keys."),
        scope="dataset",
        dimensions=("completeness", "uniqueness"),
    ),
    "DQ-CUS-003": Rule(
        rule_id="DQ-CUS-003", domain="Customer", severity="high",
        actions=("quarantine", "open_issue", "no_export"),
        summary=("Fail the gate for that row; open a steward issue; do not use "
                 "the VAT ID on a synthetic invoice or export until corrected."),
        dimensions=("consistency",),  # syntactic accuracy / format
    ),
    "DQ-PRD-001": Rule(
        rule_id="DQ-PRD-001", domain="Product", severity="high",
        actions=("quarantine", "open_issue"),
        summary=("Fail the gate; hold the product out of the product data "
                 "product; open a steward issue."),
        dimensions=("completeness",),
    ),
    "DQ-FIN-001": Rule(
        rule_id="DQ-FIN-001", domain="Finance", severity="critical",
        actions=("block_mart_row", "open_issue", "no_export"),
        summary=("Fail the gate; block the finance mart load for the row; open a "
                 "steward issue; do not publish the related KPI until resolved."),
        dimensions=("consistency",),
    ),
    "DQ-HR-001": Rule(
        rule_id="DQ-HR-001", domain="HR", severity="high",
        actions=("quarantine", "open_issue", "not_fit_for_ai", "no_export"),
        summary=("Fail the gate; quarantine the employee record; open a steward "
                 "issue; classify not_fit_for_ai; no assistant or export path."),
        dimensions=("currentness",),
    ),
}


def all_rule_ids() -> list[str]:
    return list(REGISTRY.keys())


def get(rule_id: str) -> Rule:
    return REGISTRY[rule_id]
