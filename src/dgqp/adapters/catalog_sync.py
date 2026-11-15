"""Microsoft catalog sync adapter (requirements R9.1, R9.4, R9.5).

Publishes the same glossary terms, assets and classification tags this repo
holds. The backend is chosen by ``DG_CATALOG_BACKEND`` and **defaults to
``mock``** — there is no live Microsoft catalog by default.

Reality check (docs/HYBRID.md, DESIGN.md s15.2): Microsoft Purview Data
Governance is retiring; new accounts may be uncreatable. The Fabric OneLake
catalog is the successor and is capacity-billed; a paid Fabric F SKU must not be
purchased and a Fabric trial must not be started without an explicit go. So the
default and expected backend is the mock, and a hybrid session is still a
success with the catalog mocked.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .. import governance


@dataclass
class SyncResult:
    backend: str
    terms_published: int
    tags_published: int
    live: bool
    note: str
    published_terms: list[str] = field(default_factory=list)


class CatalogSyncAdapter:
    def __init__(self) -> None:
        config.check_region()
        self.backend = config.catalog_backend()
        self.live = self.backend != "mock"

    def status(self) -> config.AdapterStatus:
        return config.AdapterStatus(
            "catalog_sync",
            self.live,
            f"backend={self.backend}" if self.live else "default mock backend",
        )

    def sync(self) -> SyncResult:
        elements = governance.catalog_elements()
        terms = [e["element_id"] for e in elements]
        tags = sorted({t for e in elements for t in e.get("classification", [])})

        if self.backend == "mock":
            return SyncResult(
                backend="mock",
                terms_published=len(terms),
                tags_published=len(tags),
                live=False,
                note="Mock catalog sync: no live Microsoft catalog by default.",
                published_terms=terms,
            )
        # pragma: no cover - a live backend needs a usable account that the
        # design does not assume exists.
        raise NotImplementedError(
            f"live catalog backend {self.backend!r} requires a usable account; "
            "default is mock (see docs/HYBRID.md and DESIGN.md s15.2)"
        )
