"""Enterprise Data Governance & Quality Platform (dgqp).

Operating-model code for the ``oss`` profile: synthetic data, ODCS contracts,
a data-quality gate, lineage, and the governance artefacts that sit around them.

The package is standard-library only so it runs in an offline CI sandbox. Where
a richer tool (Great Expectations, dbt, the official ODCS JSON Schema validator)
is available locally, the declarative artefacts under ``quality/``, ``dbt/`` and
``contracts/`` mirror the same rules; CI relies on this Python engine as the
documented unit equivalent (see design.md s10).
"""

__all__ = ["__version__"]

__version__ = "0.0.0"
