# Contributing

This is a portfolio / lab repository. A few conventions keep it honest and
reviewable.

## Commits
- Small and labelled, e.g. `phase-3: add DQ-FIN-001`.
- **No AI attribution and no `Co-authored-by`** (or similar) trailers.
- One logical change per commit.

## Branches and PRs
- Work on the `spec` branch during spec and early implementation.
- PRs target `main`. Keep the draft PR open until a phase is reviewed.

## Profiles
- `oss` is the default and the only profile CI guarantees. It is standard-library
  Python + pytest and runs with no cloud account.
- `hybrid` (Phase 9) adds optional, env-only (`DG_*`) Azure adapters, mocked in
  tests. Never commit secrets or a subscription ID.

## Offline sandbox note
CI runs with no package network access, so the repo is standard-library only.
The data-quality rules are implemented as a Python engine that CI exercises;
the Great Expectations / dbt / official ODCS JSON Schema artefacts mirror the
same rules and are the local/hybrid path. This split is the documented unit
equivalent (see `design.md` s10, `requirements.md` R1.4).

## Honesty rules (hard)
- **No invented metrics.** Every number in the README, report or case study must
  come from a committed run file under `eval/results/` carrying a UTC timestamp
  and git SHA. Until then, write `TARGET` or `TO BE MEASURED`.
- **No copied statutory or standard text.** Use rule IDs and short titles in our
  own words (see `docs/RULES-AND-POLICIES.md`).
- **Synthetic data only.** Fictional firms Northwind Advisory and Tarsfeld Group
  GmbH. HR data stays local and is never configured for an Azure source.
- Keep the published icon diagram (`docs/diagrams/architecture.png`) as the
  official figure; regenerate from `architecture.py`, never replace it with a
  box-only Mermaid diagram.

## Running locally
```
make validate   # structural validation of contracts + governance files
make test       # pytest: quality rules, schemas, lineage, workflow
make quality    # run the data-quality gate over the synthetic extracts
make scorecard  # KPI scorecard (placeholders unless a run file exists)
```
