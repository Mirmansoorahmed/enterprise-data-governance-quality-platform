"""Source adapters: Azure SQL (Finance) and Azure Blob (Product).

Each adapter has a required mock backend and an optional live backend chosen by
``DG_*`` env. With no credentials the adapter is a mock and reads the same local
synthetic extract the oss profile uses, so ``make demo`` still runs.

The HR domain is never available through an Azure source: requesting HR from any
Azure adapter raises :class:`HrLocalOnlyError` (requirements R9.4).
"""

from __future__ import annotations

import csv
import io
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import config
from .. import synthdata

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Azure resource-name charset, used to keep names out of a crafted URL.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


class HrLocalOnlyError(RuntimeError):
    """Raised if anything tries to bind or read HR through an Azure source."""


class SourceError(RuntimeError):
    """Raised on a live-source failure. Never contains the SAS or a secret."""


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


def _blob_url(account: str, container: str, blob: str, sas: str) -> str:
    """Build the blob HTTPS URL. The SAS is query-string only and is never
    returned to a caller, logged, or included in any error message.
    """
    for label, value in (("account", account), ("container", container)):
        if not _NAME_RE.match(value or ""):
            raise SourceError(f"invalid Azure storage {label} name")
    # The blob path may contain '/'; validate each segment.
    for seg in (blob or "").split("/"):
        if not _NAME_RE.match(seg):
            raise SourceError("invalid Azure blob name")
    sas = (sas or "").lstrip("?")
    return f"https://{account}.blob.core.windows.net/{container}/{blob}?{sas}"


def _http_get_text(url: str, timeout: int = 30) -> str:
    """HTTPS GET returning decoded text. Translates HTTP errors to SourceError
    without exposing the URL (which carries the SAS).
    """
    if not url.startswith("https://"):
        raise SourceError("Azure Blob source must be HTTPS")
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - https only
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        # Do not echo the URL or SAS. Map common statuses to clear guidance.
        if exc.code == 403:
            raise SourceError(
                "Azure Blob returned 403 (forbidden). Check the read-only "
                "container SAS in DG_AZURE_STORAGE_SAS: permissions, expiry and "
                "that it covers this blob."
            ) from None
        if exc.code == 404:
            raise SourceError(
                "Azure Blob returned 404 (not found). Check "
                "DG_AZURE_STORAGE_CONTAINER and DG_AZURE_STORAGE_BLOB."
            ) from None
        raise SourceError(f"Azure Blob request failed with HTTP {exc.code}") from None
    except urllib.error.URLError:
        raise SourceError("Azure Blob request failed (network/TLS error)") from None


def _rows_from_csv_text(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


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
        if self.live:
            return SourceResult(self.domain, "live", self._read_live())
        rows = synthdata.read_csv(
            os.path.join(REPO_ROOT, "data", "raw", "finance", "finance_postings.csv")
        )
        return SourceResult(self.domain, "mock", rows)

    def _read_live(self) -> list[dict]:
        """Query Azure SQL over TLS using the optional ``pymssql`` driver.

        ``pymssql`` is an optional extra (``pip install .[hybrid]``). If the
        credentials are set but the driver is missing, this raises a clear
        error — it never silently falls back to the mock. No secret is logged.
        """
        try:
            import pymssql  # type: ignore
        except ImportError:
            raise SourceError(
                "live Azure SQL read needs the optional driver: "
                "pip install pymssql (or: pip install .[hybrid]). "
                "Credentials are set, so the adapter will not silently mock."
            ) from None

        server = os.environ["DG_AZURE_SQL_SERVER"]
        database = os.environ["DG_AZURE_SQL_DATABASE"]
        user = os.environ["DG_AZURE_SQL_USER"]
        password = os.environ["DG_AZURE_SQL_PASSWORD"]
        table = config.azure_sql_table()
        if not _NAME_RE.match(table):
            raise SourceError("invalid DG_AZURE_SQL_TABLE name")

        try:
            conn = pymssql.connect(
                server=server, user=user, password=password, database=database,
                port=1433, tds_version="7.4", login_timeout=30, timeout=30,
            )
        except Exception:
            # pymssql exceptions can contain connection detail; do not propagate.
            raise SourceError(
                "Azure SQL connection failed. Check DG_AZURE_SQL_SERVER/"
                "DATABASE/USER/PASSWORD and that the firewall allows this client."
            ) from None
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f"SELECT * FROM [{table}]")
            rows = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()
        # Normalise every value to str so the rows match the mock/CSV shape.
        return [{k: ("" if v is None else str(v)) for k, v in row.items()} for row in rows]


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
        if self.live:
            return SourceResult(self.domain, "live", self._read_live())
        rows = synthdata.read_csv(
            os.path.join(REPO_ROOT, "data", "raw", "product", "products.csv")
        )
        return SourceResult(self.domain, "mock", rows)

    def _read_live(self) -> list[dict]:
        """Read the Product CSV blob over HTTPS using a read-only SAS.

        Uses only the standard library (urllib). No Azure SDK required. The SAS
        is read from DG_AZURE_STORAGE_SAS and is never logged or returned.
        """
        account = os.environ.get("DG_AZURE_STORAGE_ACCOUNT", "")
        container = os.environ.get("DG_AZURE_STORAGE_CONTAINER", "")
        sas = os.environ.get("DG_AZURE_STORAGE_SAS", "")
        if not sas:
            raise SourceError(
                "live Azure Blob read needs a read-only container SAS in "
                "DG_AZURE_STORAGE_SAS (DG_AZURE_STORAGE_KEY alone is not used "
                "by this stdlib adapter)"
            )
        blob = config.azure_storage_blob()
        url = _blob_url(account, container, blob, sas)
        text = _http_get_text(url)
        return _rows_from_csv_text(text)


def azure_source_for(domain: str):
    """Return the Azure source adapter for a domain, refusing HR."""
    _guard_not_hr(domain)
    if domain == "Finance":
        return AzureSqlSource()
    if domain == "Product":
        return AzureBlobSource()
    raise ValueError(f"no Azure source adapter for domain {domain!r}")
