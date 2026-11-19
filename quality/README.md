# Quality suites (Great Expectations declarative mirror)

Great Expectations is the declarative tool of record for the value/format/
uniqueness checks. The offline CI sandbox has no GE, so `src/dgqp/quality/`
implements the same `DQ-*` rules in standard-library Python and the test suite
exercises each rule's pass/fail, severity and on-fail action. This is the
documented unit equivalent (see `design.md` s10, `requirements.md` R3.1).

`expectations.yaml` lists each rule as a GE-style expectation so the mapping is
reviewable. When GE is available locally, these become expectation suites over
the same contracts and extracts; the dbt tests under `dbt/` cover the
relational/reference checks (`DQ-CUS-002`, `DQ-FIN-001`).
