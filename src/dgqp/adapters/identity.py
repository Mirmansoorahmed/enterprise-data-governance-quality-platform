"""Entra ID group-to-owner/role mapping adapter (requirements R9.1).

Mock backend maps synthetic group names to the RACI owner/steward roles. A live
backend (Entra app registration + group claims) is attempted only in a hybrid
session; it degrades to the mock when credentials or group claims are absent.
"""

from __future__ import annotations

from . import config

# Synthetic group -> role mapping used by the mock backend.
_MOCK_GROUP_MAP = {
    "grp-customer-owners": "Data Owner (Customer)",
    "grp-customer-stewards": "Data Steward (Datenverantwortlicher, Customer)",
    "grp-finance-owners": "Data Owner (Finance)",
    "grp-hr-owners": "Data Owner (HR)",
    "grp-dpo": "DPO (Tarsfeld, fictional)",
}


class EntraAdapter:
    def __init__(self) -> None:
        config.check_region()
        self.live = config.entra_live()

    def status(self) -> config.AdapterStatus:
        return config.AdapterStatus(
            "entra",
            self.live,
            "DG_ENTRA_* present" if self.live else "no credentials; using mock",
        )

    def role_for_group(self, group: str) -> str | None:
        if self.live:  # pragma: no cover - needs a live tenant
            raise NotImplementedError(
                "live Entra group claims run only in a hybrid session "
                "(see docs/HYBRID.md); unverified on this subscription"
            )
        return _MOCK_GROUP_MAP.get(group)
