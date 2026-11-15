"""Phase 9 — hybrid adapters (requirements R9).

* adapter-absent: with no DG_* credentials every adapter is mocked and the demo
  still runs
* HR is never bound to an Azure source (raises)
* the catalog backend defaults to mock (no live Purview/Fabric by default)
* region is Germany West Central only (other regions rejected, fail closed)
* DG_* config is environment-only; HYBRID.md has the required sections and
  leaks no subscription id / tenant name / credit amount / "IU" / "university"
"""

import os
import re

import pytest

from dgqp import demo
from dgqp.adapters import (
    catalog_sync, config, identity, monitor, sources, status,
)
from conftest import REPO_ROOT


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    # Ensure a clean, credential-free environment for the adapter-absent path.
    for key in list(os.environ):
        if key.startswith("DG_"):
            monkeypatch.delenv(key, raising=False)


# --- adapter-absent --------------------------------------------------------

def test_default_profile_is_oss():
    assert config.profile() == "oss"
    assert config.is_hybrid() is False


def test_all_adapters_mocked_without_credentials():
    assert sources.AzureSqlSource().live is False
    assert sources.AzureBlobSource().live is False
    assert identity.EntraAdapter().live is False
    assert monitor.MonitorAdapter().live is False
    assert catalog_sync.CatalogSyncAdapter().live is False
    assert status.all_mocked() is True


def test_mock_sources_read_local_extracts():
    fin = sources.AzureSqlSource().read()
    prd = sources.AzureBlobSource().read()
    assert fin.backend == "mock" and fin.rows
    assert prd.backend == "mock" and prd.rows


def test_demo_still_runs_in_hybrid_without_credentials(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    summary = demo.run(write_run=False)
    assert summary["gate_findings"] >= 6  # demo completed end to end


def test_hybrid_profile_with_no_creds_is_all_mocked(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    assert status.all_mocked() is True


# --- HR never to Azure -----------------------------------------------------

def test_hr_source_adapter_refused():
    with pytest.raises(sources.HrLocalOnlyError):
        sources.azure_source_for("HR")


def test_hr_read_guard_on_each_adapter():
    sql = sources.AzureSqlSource()
    sql.domain = "HR"  # force the guard
    with pytest.raises(sources.HrLocalOnlyError):
        sql.read()


def test_status_reports_hr_not_to_azure():
    assert status.summary()["hr_to_azure"] is False


# --- catalog default mock --------------------------------------------------

def test_catalog_backend_defaults_to_mock():
    assert config.catalog_backend() == "mock"
    result = catalog_sync.CatalogSyncAdapter().sync()
    assert result.backend == "mock"
    assert result.live is False
    assert result.terms_published >= 5


def test_catalog_live_backends_not_default(monkeypatch):
    monkeypatch.setenv("DG_CATALOG_BACKEND", "purview")
    adapter = catalog_sync.CatalogSyncAdapter()
    assert adapter.live is True
    with pytest.raises(NotImplementedError):
        adapter.sync()  # no usable account assumed; not reachable by default


def test_invalid_catalog_backend_rejected(monkeypatch):
    monkeypatch.setenv("DG_CATALOG_BACKEND", "nonsense")
    with pytest.raises(config.ConfigError):
        config.catalog_backend()


# --- region Germany West Central only --------------------------------------

def test_region_default_ok():
    config.check_region()  # no DG_AZURE_REGION set -> no raise


def test_region_rejects_other(monkeypatch):
    monkeypatch.setenv("DG_AZURE_REGION", "West Europe")
    with pytest.raises(config.ConfigError):
        config.check_region()


def test_region_accepts_germany_west_central(monkeypatch):
    monkeypatch.setenv("DG_AZURE_REGION", "Germany West Central")
    config.check_region()  # no raise


# --- env-only config + HYBRID.md -------------------------------------------

def test_config_reads_only_environment(monkeypatch):
    monkeypatch.setenv("DG_PROFILE", "hybrid")
    monkeypatch.setenv("DG_AZURE_SQL_SERVER", "s")
    monkeypatch.setenv("DG_AZURE_SQL_DATABASE", "d")
    monkeypatch.setenv("DG_AZURE_SQL_USER", "u")
    monkeypatch.setenv("DG_AZURE_SQL_PASSWORD", "p")
    assert config.azure_sql_live() is True  # purely from env


def test_hybrid_doc_has_required_sections():
    with open(os.path.join(REPO_ROOT, "docs", "HYBRID.md"), encoding="utf-8") as fh:
        text = fh.read()
    for needed in ("Germany West Central", "Teardown", "Results",
                   "TO BE MEASURED (live session pending)",
                   "DG_PROFILE", "create", "delete"):
        assert needed in text, needed


def test_hybrid_doc_leaks_no_identifiers():
    with open(os.path.join(REPO_ROOT, "docs", "HYBRID.md"), encoding="utf-8") as fh:
        text = fh.read()
    low = text.lower()
    assert "university" not in low
    assert re.search(r"\biu\b", low) is None
    assert "azure for students" not in low
    assert "$90" not in text and "usd 90" not in low
    # no GUID-like subscription id
    assert re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", low) is None


def test_no_fabric_trial_or_paid_sku_instruction():
    with open(os.path.join(REPO_ROOT, "docs", "HYBRID.md"), encoding="utf-8") as fh:
        raw = fh.read().lower().replace("*", "")
    text = " ".join(raw.split())  # drop markdown emphasis + collapse whitespace
    assert "not start a fabric trial" in text
    assert "paid fabric f sku" in text
