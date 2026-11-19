"""Phase 9b — live hybrid backends with mocked HTTP and a fake pymssql.

No network and no real driver are used. These tests inject:
* a fake ``urllib.request.urlopen`` for the Blob HTTPS read
* a fake ``pymssql`` module for the Azure SQL read

They verify the live rows match the mock shape, the gate runs over live rows,
403/404 give clean secret-free errors, creds-set-but-driver-missing does not
silently mock, HR stays untouched, and the smoke run file records no secrets.
"""

import io
import json
import os
import sys
import urllib.error

import pytest

from dgqp.adapters import config, smoke, sources
from dgqp.quality import gate
from conftest import REPO_ROOT


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith("DG_"):
            monkeypatch.delenv(key, raising=False)


def _hybrid_blob_env(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    monkeypatch.setenv("DG_AZURE_REGION", "Germany West Central")
    monkeypatch.setenv("DG_AZURE_STORAGE_ACCOUNT", "acct")
    monkeypatch.setenv("DG_AZURE_STORAGE_CONTAINER", "cont")
    monkeypatch.setenv("DG_AZURE_STORAGE_SAS", "sv=2024&sig=FAKESECRET")


def _hybrid_sql_env(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    monkeypatch.setenv("DG_AZURE_REGION", "Germany West Central")
    monkeypatch.setenv("DG_AZURE_SQL_SERVER", "srv.database.windows.net")
    monkeypatch.setenv("DG_AZURE_SQL_DATABASE", "db")
    monkeypatch.setenv("DG_AZURE_SQL_USER", "u")
    monkeypatch.setenv("DG_AZURE_SQL_PASSWORD", "PW-SECRET-VALUE")


# --- live Blob (mocked HTTP) ----------------------------------------------

class _FakeResp:
    def __init__(self, body: str, status: int = 200):
        self._body = body.encode()
        self.status = status

    def read(self):
        return self._body

    class _Headers:
        @staticmethod
        def get_content_charset():
            return "utf-8"

    @property
    def headers(self):
        return self._Headers()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_live_blob_read_parses_csv(monkeypatch):
    _hybrid_blob_env(monkeypatch)
    csv_text = ("product_id,company,name,status,unit_of_measure\n"
                "P-1,DE01,Widget,active,EA\n"
                "P-2,DE01,,active,\n")  # second row fails DQ-PRD-001
    captured = {}

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        return _FakeResp(csv_text)

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake_urlopen)
    src = sources.AzureBlobSource()
    assert src.live is True
    result = src.read()
    assert result.backend == "live"
    assert [r["product_id"] for r in result.rows] == ["P-1", "P-2"]
    # URL built correctly and carries the SAS, but it is only in the request.
    assert captured["url"].startswith("https://acct.blob.core.windows.net/cont/products.csv?")
    # gate runs over the live rows
    g = gate.check_product_rows(result.rows)
    assert len(g.findings) == 1


def test_live_blob_custom_blob_name(monkeypatch):
    _hybrid_blob_env(monkeypatch)
    monkeypatch.setenv("DG_AZURE_STORAGE_BLOB", "sub/products-latest.csv")
    seen = {}

    def fake_urlopen(req, timeout=30):
        seen["url"] = req.full_url
        return _FakeResp("product_id,company,name,status,unit_of_measure\nP-9,DE01,X,active,EA\n")

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake_urlopen)
    sources.AzureBlobSource().read()
    assert "/cont/sub/products-latest.csv?" in seen["url"]


def test_live_blob_403_clean_error_no_secret(monkeypatch):
    _hybrid_blob_env(monkeypatch)

    def fake_urlopen(req, timeout=30):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(sources.SourceError) as exc:
        sources.AzureBlobSource().read()
    msg = str(exc.value)
    assert "403" in msg
    assert "FAKESECRET" not in msg and "sig=" not in msg


def test_live_blob_404_clean_error(monkeypatch):
    _hybrid_blob_env(monkeypatch)

    def fake_urlopen(req, timeout=30):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(sources.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(sources.SourceError) as exc:
        sources.AzureBlobSource().read()
    assert "404" in str(exc.value)
    assert "FAKESECRET" not in str(exc.value)


def test_live_blob_requires_sas(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    monkeypatch.setenv("DG_AZURE_STORAGE_ACCOUNT", "acct")
    monkeypatch.setenv("DG_AZURE_STORAGE_CONTAINER", "cont")
    monkeypatch.setenv("DG_AZURE_STORAGE_KEY", "key-only-no-sas")
    src = sources.AzureBlobSource()
    assert src.live is True  # KEY makes it "configured"
    with pytest.raises(sources.SourceError) as exc:
        src.read()  # but the stdlib adapter needs a SAS
    assert "SAS" in str(exc.value)


# --- live SQL (fake pymssql) ----------------------------------------------

class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql):
        self.sql = sql

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows
        self.closed = False

    def cursor(self, as_dict=False):
        assert as_dict is True
        return _FakeCursor(self._rows)

    def close(self):
        self.closed = True


def _install_fake_pymssql(monkeypatch, rows, fail=False):
    import types
    mod = types.ModuleType("pymssql")

    def connect(**kwargs):
        if fail:
            raise RuntimeError("boom with server detail and password")
        # TLS/driver params present
        assert kwargs.get("port") == 1433
        return _FakeConn(rows)

    mod.connect = connect
    monkeypatch.setitem(sys.modules, "pymssql", mod)


def test_live_sql_read_via_fake_pymssql(monkeypatch):
    _hybrid_sql_env(monkeypatch)
    rows = [
        {"posting_id": "F-1", "company": "DE01", "cost_centre_id": "CC-1000", "amount": 100},
        {"posting_id": "F-4", "company": "DE01", "cost_centre_id": "CC-9999", "amount": 75},
    ]
    _install_fake_pymssql(monkeypatch, rows)
    src = sources.AzureSqlSource()
    assert src.live is True
    result = src.read()
    assert result.backend == "live"
    # values normalised to str to match the mock/CSV shape
    assert result.rows[0]["amount"] == "100"
    assert all(isinstance(v, str) for v in result.rows[0].values())
    g = gate.check_finance_rows(result.rows)
    assert len(g.findings) == 1  # CC-9999 unknown


def test_live_sql_creds_set_but_driver_missing_does_not_mock(monkeypatch):
    _hybrid_sql_env(monkeypatch)
    monkeypatch.setitem(sys.modules, "pymssql", None)  # force ImportError
    src = sources.AzureSqlSource()
    with pytest.raises(sources.SourceError) as exc:
        src.read()
    assert "pip install" in str(exc.value)


def test_live_sql_connection_error_is_secret_free(monkeypatch):
    _hybrid_sql_env(monkeypatch)
    _install_fake_pymssql(monkeypatch, [], fail=True)
    with pytest.raises(sources.SourceError) as exc:
        sources.AzureSqlSource().read()
    # The secret VALUE and the raw driver exception must not leak (the error may
    # still name the env var DG_AZURE_SQL_PASSWORD as guidance).
    assert "PW-SECRET-VALUE" not in str(exc.value)
    assert "boom" not in str(exc.value).lower()


def test_live_sql_rejects_bad_table_name(monkeypatch):
    _hybrid_sql_env(monkeypatch)
    monkeypatch.setenv("DG_AZURE_SQL_TABLE", "bad; DROP TABLE x")
    _install_fake_pymssql(monkeypatch, [])
    with pytest.raises(sources.SourceError) as exc:
        sources.AzureSqlSource().read()
    assert "table" in str(exc.value).lower()


# --- HR untouched ----------------------------------------------------------

def test_smoke_asserts_hr_untouched(monkeypatch):
    # The smoke run asserts HR has no Azure adapter.
    summary = smoke.run()
    assert summary["hr_to_azure"] is False


def test_hr_has_no_azure_adapter():
    with pytest.raises(sources.HrLocalOnlyError):
        sources.azure_source_for("HR")


# --- smoke run file: no secrets -------------------------------------------

def test_smoke_run_file_has_no_secrets(monkeypatch, tmp_path):
    _hybrid_blob_env(monkeypatch)
    monkeypatch.setenv("DG_AZURE_SQL_SERVER", "srv.database.windows.net")
    monkeypatch.setenv("DG_AZURE_SQL_DATABASE", "db")
    monkeypatch.setenv("DG_AZURE_SQL_USER", "u")
    monkeypatch.setenv("DG_AZURE_SQL_PASSWORD", "topsecret")

    # Blob live via mocked HTTP; SQL stays live-configured but we only inspect
    # the run-file content for leaks, so route SQL to the mock by removing creds
    # is not needed — we just must not leak. Mock the blob fetch:
    monkeypatch.setattr(
        sources.urllib.request, "urlopen",
        lambda req, timeout=30: _FakeResp(
            "product_id,company,name,status,unit_of_measure\nP-1,DE01,W,active,EA\n"
        ),
    )
    # Avoid a real pymssql import attempt by making Finance mock: drop SQL creds.
    monkeypatch.delenv("DG_AZURE_SQL_SERVER", raising=False)
    monkeypatch.delenv("DG_AZURE_SQL_DATABASE", raising=False)
    monkeypatch.delenv("DG_AZURE_SQL_USER", raising=False)
    monkeypatch.delenv("DG_AZURE_SQL_PASSWORD", raising=False)

    summary = smoke.run()
    monkeypatch.setattr(smoke, "RESULTS_DIR", str(tmp_path))
    path = smoke.write_run(summary)
    blob = open(path, encoding="utf-8").read().lower()
    # No secret value, SAS, account/server name or subscription id in the file.
    for leak in ("topsecret", "fakesecret", "sig=", "acct.blob",
                 "database.windows.net"):
        assert leak not in blob, leak
    data = json.loads(open(path, encoding="utf-8").read())
    assert data["kind"] == "hybrid"
    assert "live" in data["metrics"] and "mock" in data["metrics"]


# --- seed script -----------------------------------------------------------

def test_seed_script_generates_synthetic_only(monkeypatch, tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hybrid_seed", os.path.join(REPO_ROOT, "scripts", "hybrid_seed.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sql = mod.build_sql()
    assert "CREATE TABLE dbo.finance_postings" in sql
    assert "INSERT INTO dbo.finance_postings" in sql
    # synthetic finance ids present; no HR token
    assert "F-1" in sql and "F-4" in sql
    assert "employee" not in sql.lower() and "pii.hr" not in sql.lower()
