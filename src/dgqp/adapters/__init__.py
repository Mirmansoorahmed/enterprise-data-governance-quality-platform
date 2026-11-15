"""Hybrid Azure adapters (Phase 9, requirements R9).

Optional, feature-flagged, environment-only (``DG_*``) adapters. Everything
defaults to a mock. With no ``DG_*`` credentials set, every adapter resolves to
its mock and ``make demo`` still runs on the oss path. Tests exercise the
adapter-absent path.

Hard rules enforced here and in the adapters:
* region is Germany West Central only
* the HR domain is never bound to an Azure source
* the catalog backend defaults to ``mock`` (no live Purview/Fabric by default)
* no secret is read from anywhere but the environment; nothing is committed

The oss profile does not import live Azure SDKs. The adapters define the
interface and a mock backend; a live backend is wired on a machine that has the
SDKs and real credentials, during a create-test-delete portal session
(docs/HYBRID.md). This package is standard-library only.
"""
