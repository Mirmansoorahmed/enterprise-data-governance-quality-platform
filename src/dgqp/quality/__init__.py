"""Data-quality gate: the DQ-* rule checks, registry and fail-closed executor.

The rules here are the canonical, testable implementation of the catalog in
``docs/RULES-AND-POLICIES.md``. The Great Expectations suites and dbt tests
under ``quality/`` and ``dbt/`` mirror the same rules; the offline CI sandbox
exercises this Python engine as the documented unit equivalent (design s10).
"""
