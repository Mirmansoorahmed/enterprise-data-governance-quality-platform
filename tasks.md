# Tasks — Enterprise Data Governance & Quality Platform

**Branch:** `spec` · **Status:** plan for review; no implementation until Mir says go.
**Order:** Phases 0–8 on `oss` first, Phase 9 (`hybrid`) last. Each phase must be demoable on its own. Prefer small, testable slices. Tests sit next to each slice. Commits small and labelled (e.g. `phase-3: add DQ-FIN-001`); no `Co-authored-by`, no AI attribution.

Traceability: requirements in [`requirements.md`](requirements.md); design in [`design.md`](design.md); rule IDs in [`docs/RULES-AND-POLICIES.md`](docs/RULES-AND-POLICIES.md).

---

## Phase 0 — Repo foundation _(R8, NFR1–9)_
- [ ] 0.1 Add `Makefile` targets: `pull`/`bootstrap` (one-time), `demo`, `report`, `test`, `validate`. _(R8.1)_
- [ ] 0.2 Add `docker-compose.yml` skeleton for local OpenMetadata + deps (not required in CI). _(R4.1)_
- [ ] 0.3 Add JSON schemas: ODCS validation wiring, `label-pack`, `ropa`, `raci`, `run-file`. _(R1.4, R5.3, R7.2)_
- [ ] 0.4 Add CI workflow (`oss` only): schema validation, dbt tests, GE/unit, workflow, label, adapter-absent, scorecard print. _(design §10)_
- [ ] 0.5 Confirm docs placement (`docs/DESIGN.md`, `CASE-STUDY.md`, `RULES-AND-POLICIES.md`, `diagrams/`) and keep the icon figure as published. _(R8.4)_
- [ ] 0.6 Document commit conventions and the no-AI-attribution rule in `CONTRIBUTING`/README. _(NFR8)_
- **Test hooks:** CI runs green on an empty pipeline; schema files validate against trivial fixtures.
- **Demoable:** `make test` and CI pass on a skeleton.

## Phase 1 — Synthetic data + ODCS contracts _(R1)_
- [ ] 1.1 Generate synthetic extracts for four domains, two country companies, with seeded defects for every `DQ-*` rule. _(R1.1, R1.2)_
- [ ] 1.2 Add the Finance company-code / cost-centre reference list. _(R1.2, R3)_
- [ ] 1.3 Author one ODCS v3.2.0 contract per domain product + reference lists; custom props for policy IDs, classification, owner, steward, retention, VAT pattern. _(R1.3)_
- [ ] 1.4 Wire official ODCS v3.2.0 schema validation into `make validate` and CI. _(R1.4)_
- [ ] 1.5 Assert HR has no Azure source binding. _(R1.5)_
- **Test hooks:** schema validation per contract; defect-presence tests; HR-no-Azure test.
- **Demoable:** show dirty extracts + validated contracts.

## Phase 2 — dbt marts + lineage _(R2)_
- [ ] 2.1 dbt project + domain marts, one KPI dataset per domain. _(R2.1)_
- [ ] 2.2 Record lineage source → mart → scorecard per KPI dataset. _(R2.2)_
- [ ] 2.3 Wire `DQ-FIN-001` so a failing row is held from the finance mart and its KPI. _(R2.3)_
- **Test hooks:** lineage-present (binary) test; `DQ-FIN-001` hold-back test.
- **Demoable:** build marts, show lineage for one KPI per domain.

## Phase 3 — Quality gate + scorecard _(R3)_
- [ ] 3.1 Rule registry: each `DQ-*` → check, severity, on-fail action. _(R3.1)_
- [ ] 3.2 GE suites: `DQ-CUS-001/003`, `DQ-PRD-001`, `DQ-HR-001`. _(R3.1)_
- [ ] 3.3 dbt tests: `DQ-CUS-002` uniqueness across companies, `DQ-FIN-001` reference + reconciliation. _(R3.1)_
- [ ] 3.4 Fail-closed executor: quarantine/block + open steward issue; withhold `fit_for_ai` where required. _(R3.2)_
- [ ] 3.5 Scorecard (completeness, uniqueness, consistency, currentness + cross-domain key match); render `TARGET`/`TO BE MEASURED` with no run file. _(R3.3, R3.4)_
- [ ] 3.6 Document the VAT per-country pattern as a contract parameter, not official. _(R3.5)_
- **Test hooks:** one pass/fail + severity + action test per rule; scorecard-placeholder test.
- **Demoable:** run the rule pack, show the scorecard.

## Phase 4 — Catalog, glossary, ownership _(R4)_
- [ ] 4.1 Glossary terms EN + DE aliases; one critical element per domain minimum. _(R4.1)_
- [ ] 4.2 RACI register (`GOV-RACI-01`): owner + steward per critical element. _(R4.2)_
- [ ] 4.3 `GOV-META-01`: link definition + metadata + classification + contract + rule. _(R4.3)_
- [ ] 4.4 `GOV-MDM-01`: documented SoR + create-change-approve for `customer_id`/`product_id`; SAP MDG as buy note only. _(R4.4)_
- [ ] 4.5 Recorded catalog fixtures so CI needs no live OpenMetadata. _(R4.1)_
- [ ] 4.6 Bilingual steward label; assert steward ≠ GDPR controller. _(R4.5)_
- **Test hooks:** every critical element resolves owner/steward/definition/classification/contract/rule; CI-needs-no-OpenMetadata test.
- **Demoable:** open catalog (or fixtures), show definitions + ownership.

## Phase 5 — Classification, RoPA, retention, access _(R5)_
- [ ] 5.1 Apply tag set and assignments. _(R5.1)_
- [ ] 5.2 Implement `POL-GDPR-01…06`, each mapped to a check/workflow. _(R5.2)_
- [ ] 5.3 Customer + HR RoPA with Art. 30(1) field set, schema-validated. _(R5.3)_
- [ ] 5.4 Retention threshold → flag only; no production deletion. _(R5.4)_
- [ ] 5.5 Access policy checks; keep mappings illustrative (ID + own-words title). _(R5.2, R5.5)_
- **Test hooks:** RoPA schema test; retention-flag-only test; doc-lint test against copied statutory text.
- **Demoable:** show classification, RoPA and a retention flag.

## Phase 6 — Steward issue / cleanse workflow _(R6)_
- [ ] 6.1 Issue model: rule ID, record key, severity, timestamp. _(R6.1)_
- [ ] 6.2 Decision (cleanse/exception) + documented cleanse + re-run. _(R6.2)_
- [ ] 6.3 Close on resolution; auditable exception path. _(R6.3)_
- [ ] 6.4 Record issue-cycle process metric to a run file. _(R6, R8.5)_
- **Test hooks:** end-to-end fail→issue→decision→cleanse→re-run→pass; exception-auditable test.
- **Demoable:** fix one failed record live and re-run the rule.

## Phase 7 — AI label export _(R7)_
- [ ] 7.1 `AI-FIT-01` gate (owner+steward, classification, DQ, POL-GDPR-01/02/04/06, lineage). _(R7.1)_
- [ ] 7.2 Versioned label pack + schema + exporter. _(R7.2)_
- [ ] 7.3 Fixture consumer: §9 deny/ask/allow outcomes. _(R7.3)_
- [ ] 7.4 Assert no PEP, no prompt bodies, no sibling-repo writes. _(R7.4)_
- **Test hooks:** gate-logic test; schema-valid label pack; deny/ask/allow fixture tests; no-sibling-write test.
- **Demoable:** export labels, replay the gateway fixture.

## Phase 8 — Demo, report, eval, README _(R8)_
- [ ] 8.1 `make demo` runs the §9 script on `oss` under 15 min after pull; write duration run file. _(R8.2, R8.5)_
- [ ] 8.2 `make report` PDF pack; fail closed on missing field / unsourced number. _(R8.3)_
- [ ] 8.3 `eval/results/` persistence with UTC timestamp + git SHA; README reads only committed figures. _(R8.5)_
- [ ] 8.4 README ~3-min skim: problem → icon figure → run (both profiles) → results → limitations. _(R8.6)_
- [ ] 8.5 Keep/regenerate published icon figures from `architecture.py`; never a box-only Mermaid replacement. _(R8.4)_
- **Test hooks:** timed-demo writes duration; report fail-closed tests; diagram-present-and-referenced test.
- **Demoable:** full `make demo` + `make report`.

## Phase 9 — Hybrid adapters + HYBRID.md _(R9)_ — last, only on explicit go
- [ ] 9.1 Adapter interfaces + required mocks: Azure SQL (Finance), Blob (Product), Entra, Azure Monitor, catalog sync. _(R9.1)_
- [ ] 9.2 `DG_*` env-only config; absent creds → mocks; `make demo` still runs. _(R9.2)_
- [ ] 9.3 Enforce region Germany West Central, portal-only, auto-pause, create-test-delete; no HR→Azure; catalog default mock; no Fabric trial / paid F SKU. _(R9.3, R9.4)_
- [ ] 9.4 `docs/HYBRID.md`: portal steps, env vars, cost notes, teardown checklist, results section (post-session only; live vs mock separated; no subscription ID; no secrets). _(R9.5)_
- [ ] 9.5 Purview/Fabric reality check wording; default no live Microsoft catalog. _(design §9.1)_
- **Test hooks:** adapter-absent tests; HR-no-Azure test; catalog-default-mock test.
- **Demoable (mock):** `make demo` with `DG_*` unset uses mocks; live session only with explicit go, then teardown.

---

## Definition of done (per phase)
Tests next to the slice pass; CI green on `oss`; no invented numbers; no copied statutory text; commits small, labelled, no AI attribution; the phase is demoable on its own.
