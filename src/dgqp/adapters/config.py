"""DG_* environment configuration for the hybrid profile (requirements R9.2/R9.3).

All hybrid configuration is read from environment variables prefixed ``DG_``.
Nothing is read from a committed file; no secret is stored in the repo. When a
variable is absent the adapter degrades to its mock.

The only allowed Azure region is Germany West Central. A configuration that
names any other region is rejected (fail closed) rather than silently used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ALLOWED_REGION = "germanywestcentral"

# The HR domain must never be bound to an Azure source.
HR_DOMAIN = "HR"
AZURE_BOUND_DOMAINS = ("Finance", "Product")  # Finance -> SQL, Product -> Blob


class ConfigError(ValueError):
    """Raised for a disallowed hybrid configuration (e.g. wrong region)."""


def profile() -> str:
    """Active profile: ``oss`` (default) or ``hybrid``."""
    return os.environ.get("DG_PROFILE", "oss").strip().lower() or "oss"


def is_hybrid() -> bool:
    return profile() == "hybrid"


def _region() -> str | None:
    value = os.environ.get("DG_AZURE_REGION")
    if value is None:
        return None
    return value.strip().lower().replace(" ", "")


def check_region() -> None:
    """Fail closed if a region is set and is not Germany West Central."""
    region = _region()
    if region is not None and region != ALLOWED_REGION:
        raise ConfigError(
            f"DG_AZURE_REGION must be Germany West Central (got {region!r})"
        )


@dataclass(frozen=True)
class AdapterStatus:
    name: str
    live: bool
    reason: str


def _present(*keys: str) -> bool:
    return all(os.environ.get(k) for k in keys)


def azure_sql_live() -> bool:
    return is_hybrid() and _present(
        "DG_AZURE_SQL_SERVER", "DG_AZURE_SQL_DATABASE",
        "DG_AZURE_SQL_USER", "DG_AZURE_SQL_PASSWORD",
    )


def azure_blob_live() -> bool:
    return is_hybrid() and _present(
        "DG_AZURE_STORAGE_ACCOUNT", "DG_AZURE_STORAGE_CONTAINER",
    ) and (os.environ.get("DG_AZURE_STORAGE_KEY") or os.environ.get("DG_AZURE_STORAGE_SAS"))


def entra_live() -> bool:
    return is_hybrid() and _present(
        "DG_ENTRA_TENANT_ID", "DG_ENTRA_CLIENT_ID",
    )


def monitor_live() -> bool:
    return is_hybrid() and _present("DG_AZURE_MONITOR_WORKSPACE_ID")


def catalog_backend() -> str:
    """Catalog sync backend: defaults to ``mock``. Never live by default."""
    backend = os.environ.get("DG_CATALOG_BACKEND", "mock").strip().lower() or "mock"
    if backend not in ("mock", "purview", "fabric"):
        raise ConfigError(f"DG_CATALOG_BACKEND must be mock|purview|fabric (got {backend!r})")
    return backend
