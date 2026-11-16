"""Command-line entry points for the oss profile.

Subcommands
-----------
``validate``      Structurally validate every ODCS contract and governance file.
``scorecard``     Print the KPI scorecard (placeholders unless a run file exists).
``hybrid-smoke``  Read non-HR domains from the configured adapters (live or mock),
                  run the quality gate, and write a hybrid run file.

Standard-library only, so it runs in the offline CI sandbox. Usage::

    python -m dgqp.cli validate
    python -m dgqp.cli scorecard
    python -m dgqp.cli hybrid-smoke
"""

from __future__ import annotations

import os
import sys

from . import validate as _validate
from . import yaml_min
from .scorecard import render_scorecard

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMAS = os.path.join(REPO_ROOT, "schemas")
CONTRACTS = os.path.join(REPO_ROOT, "contracts")
GOVERNANCE = os.path.join(REPO_ROOT, "governance")


def _validate_contracts() -> list[str]:
    errors: list[str] = []
    schema = _validate.load_schema(os.path.join(SCHEMAS, "odcs-contract.schema.json"))
    if not os.path.isdir(CONTRACTS):
        return errors
    for name in sorted(os.listdir(CONTRACTS)):
        if not name.endswith((".yaml", ".yml")):
            continue
        path = os.path.join(CONTRACTS, name)
        try:
            data = yaml_min.load_file(path)
            _validate.validate(data, schema)
        except (yaml_min.YamlError, _validate.ValidationError) as exc:
            errors.append(f"{name}: {exc}")
    return errors


def _validate_governance() -> list[str]:
    errors: list[str] = []
    checks = [
        (os.path.join(GOVERNANCE, "raci", "register.yaml"), "raci.schema.json"),
        (os.path.join(GOVERNANCE, "ropa", "ropa.yaml"), "ropa.schema.json"),
    ]
    for path, schema_name in checks:
        if not os.path.exists(path):
            continue
        schema = _validate.load_schema(os.path.join(SCHEMAS, schema_name))
        try:
            data = yaml_min.load_file(path)
            _validate.validate(data, schema)
        except (yaml_min.YamlError, _validate.ValidationError) as exc:
            errors.append(f"{os.path.relpath(path, REPO_ROOT)}: {exc}")
    return errors


def cmd_validate() -> int:
    errors = _validate_contracts() + _validate_governance()
    if errors:
        for err in errors:
            print(f"INVALID  {err}", file=sys.stderr)
        print(f"\n{len(errors)} file(s) failed validation.", file=sys.stderr)
        return 1
    print("All contracts and governance files validate.")
    return 0


def cmd_scorecard() -> int:
    print(render_scorecard())
    return 0


def cmd_hybrid_smoke(write: bool = True) -> int:
    from .adapters import smoke

    summary = smoke.run()
    print(f"Hybrid smoke — profile={summary['profile']}, region={summary['region']}, "
          f"HR-to-Azure={summary['hr_to_azure']}")
    for a in summary["adapters"]:
        print(f"  adapter {a['name']}: {'live' if a['live'] else 'mock'}")
    for d in summary["domains"]:
        print(f"  {d['domain']} [{d['backend']}]: {d['row_count']} rows, "
              f"{d['gate_rule']} findings={d['gate_findings']}")
    if write:
        path = smoke.write_run(summary)
        print(f"\nWrote {os.path.relpath(path, REPO_ROOT)} "
              f"(live and mock separated; no secrets recorded).")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    command = argv[0]
    if command == "validate":
        return cmd_validate()
    if command == "scorecard":
        return cmd_scorecard()
    if command == "hybrid-smoke":
        return cmd_hybrid_smoke(write="--no-write" not in argv)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
