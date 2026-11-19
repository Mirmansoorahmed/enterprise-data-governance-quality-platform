"""Hybrid adapter status summary (requirements R9.2).

Reports which adapters are live vs mocked without touching any live service, so
``make demo`` can print the hybrid posture and still run when credentials are
absent (everything mocked). Never blends live and mock numbers.
"""

from __future__ import annotations

from . import config
from .catalog_sync import CatalogSyncAdapter
from .identity import EntraAdapter
from .monitor import MonitorAdapter
from .sources import AzureBlobSource, AzureSqlSource


def summary() -> dict:
    config.check_region()
    adapters = [
        AzureSqlSource().status(),
        AzureBlobSource().status(),
        EntraAdapter().status(),
        MonitorAdapter().status(),
        CatalogSyncAdapter().status(),
    ]
    return {
        "profile": config.profile(),
        "region": config.ALLOWED_REGION,
        "hr_to_azure": False,  # always: HR is local-only
        "adapters": [
            {"name": a.name, "live": a.live, "reason": a.reason} for a in adapters
        ],
    }


def all_mocked(status: dict | None = None) -> bool:
    status = status or summary()
    return not any(a["live"] for a in status["adapters"])
