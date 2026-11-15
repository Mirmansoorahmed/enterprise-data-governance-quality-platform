# dbt project (declarative mirror)

dbt is the tool of record for the domain marts and lineage. One KPI dataset per
domain, source → mart → scorecard (requirements R2).

The offline CI sandbox has no dbt, so the Python transforms in
`src/dgqp/marts.py` build the same marts and enforce the same gate behaviour
(a `DQ-FIN-001` failing row is held out of the finance mart and its KPI), and
`src/dgqp/lineage.py` reads the machine-readable `lineage.yaml`. This split is
the documented unit equivalent (see `design.md` s10).

When dbt is available locally, the models and `schema.yml` tests here mirror the
`DQ-*` rules; `lineage.yaml` is the single source of lineage for the catalog and
report.

## Layout
- `lineage.yaml` — source → mart → scorecard descriptors, one KPI per domain.
- `models/` — dbt model stubs per domain (added with the live dbt path).
