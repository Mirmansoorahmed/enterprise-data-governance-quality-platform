"""Optional Azure Monitor / Log Analytics evidence sink (requirements R9.1).

Mock backend records evidence events in memory. A live backend would post to a
Log Analytics workspace; it is optional and degrades to the mock when no
workspace id is set.
"""

from __future__ import annotations

from . import config


class MonitorAdapter:
    def __init__(self) -> None:
        config.check_region()
        self.live = config.monitor_live()
        self._events: list[dict] = []

    def status(self) -> config.AdapterStatus:
        return config.AdapterStatus(
            "azure_monitor",
            self.live,
            "DG_AZURE_MONITOR_* present" if self.live else "no workspace; using mock",
        )

    def emit(self, event: dict) -> None:
        if self.live:  # pragma: no cover - needs a live workspace
            raise NotImplementedError(
                "live Azure Monitor ingestion runs only in a hybrid session "
                "(see docs/HYBRID.md)"
            )
        self._events.append(dict(event))

    @property
    def events(self) -> list[dict]:
        return list(self._events)
