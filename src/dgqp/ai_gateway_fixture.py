"""Fixture consumer standing in for AI Compliance Automation / the gateway.

This is NOT the policy enforcement point. The real allow/ask/deny decision lives
in the sibling AI Compliance Automation and Agent Access Governance Gateway
repos. This fixture only replays how such a consumer WOULD read the label pack
this repo publishes (DESIGN.md s8, s9 step 5), so the demo can show the bridge
end to end. It does not store prompt bodies and never writes to a sibling repo.

Decision policy replayed (illustrative):
* a request touching ``not_fit_for_ai`` data            -> deny
* a request touching ``pii.hr``                          -> deny
* a request touching ``pii.contact`` / ``confidential.finance`` -> ask
* a request on an already-approved, non-PII KPI aggregate (fit_for_ai, no PII)
  -> allow

Standard-library only.
"""

from __future__ import annotations

from dataclasses import dataclass

DENY = "deny"
ASK = "ask"
ALLOW = "allow"

_PII_DENY = ("pii.hr",)
_PII_ASK = ("pii.contact", "confidential.finance")


@dataclass(frozen=True)
class Decision:
    outcome: str
    reason: str


def _labels_by_field(pack: dict) -> dict[str, dict]:
    return {lbl["field"]: lbl for lbl in pack["labels"]}


def decide(pack: dict, requested_fields: list[str]) -> Decision:
    """Replay a consumer decision over the requested fields.

    Precedence: a single not_fit_for_ai or pii.hr field denies the whole
    request; otherwise a pii.contact / confidential.finance field makes it ask;
    otherwise, if every field is fit_for_ai and non-PII, allow.
    """
    by_field = _labels_by_field(pack)
    saw_ask = False
    all_fit_non_pii = True

    for field in requested_fields:
        label = by_field.get(field)
        if label is None:
            return Decision(DENY, f"unknown field {field!r}: no published label")
        classification = label.get("classification", [])
        if "not_fit_for_ai" in classification or not label.get("fit_for_ai"):
            return Decision(DENY, f"{field} is not_fit_for_ai")
        if any(tag in classification for tag in _PII_DENY):
            return Decision(DENY, f"{field} carries sensitive HR PII")
        if any(tag in classification for tag in _PII_ASK):
            saw_ask = True
            all_fit_non_pii = False

    if saw_ask:
        return Decision(ASK, "request touches contact PII or confidential finance data")
    if all_fit_non_pii:
        return Decision(ALLOW, "all requested fields are fit_for_ai and non-PII")
    return Decision(ASK, "request requires review")
