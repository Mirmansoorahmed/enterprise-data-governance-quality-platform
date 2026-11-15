"""Source adapters: Azure SQL (Finance) and Azure Blob (Product).

Each adapter has a required mock backend and an optional live backend chosen by
``DG_*`` env. With no credentials the adapter is a mock and reads the same local
synthetic extract the oss profile uses, so ``make demo`` still runs.

The HR domain is never available through an Azure source: requesting HR from any
Azure adapter raises :class:`HrLocalOnlyError` (requirements R9.4).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from . import config
from .. import synthdata

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class HrLocalOnlyError(RuntimeError):
    """Raised if anything tries to bind or read HR through an Azure source."""


@dataclass
class SourceResult:
    domain: str
    backend: str          # "mock" or "live"
    rows: list[dict]


def _guard_not_hr(domain: str) -> None:
    if domain == config.HR_DOMAIN:
        raise HrLocalOnlyError(
            "HR is local-only and must never be loaded from an Azure source"
        )


class AzureSqlSource:
    """Finance source. Live backend would query Azure SQL; mock reads the local
    finance extract.
    """

    domain = "Finance"

    def __init__(self) -> None:
        config.check_region()
        self.live = config.azure_sql_live()

    def status(self) -> config.AdapterStatus:
        return config.AdapterStatus(
            "azure_sql",
            self.live,
            "DG_AZURE_SQL_* present" if self.live else "no credentials; using mock",
        )

    def read(self) -> SourceResult:
        _guard_not_hr(self.domain)
        if self.live:  # pragma: no cover - needs a live Azure session
            raise NotImplementedError(
                "live Azure SQL read runs only in a portal create-test-delete "
                "session with the Azure SDK installed (see docs/HYBRID.md)"
            )
        rows = synthdata.read_csv(
            os.path.join(REPO_ROOT, "data", "raw", "finance", "finance_postings.csv")
        )
        return SourceResult(self.domain, "mock", rows)


class AzureBlobSource:
    """Product source. Live backend would read blobs; mock reads the local
    product extract.
    """

    domain = "Product"

    def __init__(self) -> None:
        config.check_region()
        self.live = config.azure_blob_live()

    def status(self) -> config.AdapterStatus:
        return config.AdapterStatus(
            "azure_blob",
            self.live,
            "DG_AZURE_STORAGE_* present" if self.live else "no credentials; using mock",
        )

    def read(self) -> SourceResult:
        _guard_not_hr(self.domain)
        if self.live:  # pragma: no cover - needs a live Azure session
            raise NotImplementedError(
                "live Azure Blob read runs only in a portal create-test-delete "
                "session with the Azure SDK installed (see docs/HYBRID.md)"
            )
        rows = synthdata.read_csv(
            os.path.join(REPO_ROOT, "data", "raw", "product", "products.csv")
        )
        return SourceResult(self.domain, "mock", rows)


def azure_source_for(domain: str):
    """Return the Azure source adapter for a domain, refusing HR."""
    _guard_not_hr(domain)
    if domain == "Finance":
        return AzureSqlSource()
    if domain == "Product":
        return AzureBlobSource()
    raise ValueError(f"no Azure source adapter for domain {domain!r}")
