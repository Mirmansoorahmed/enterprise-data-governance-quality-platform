# Design — Enterprise Data Governance & Quality Platform

**Repo:** `enterprise-data-governance-quality-platform` · **Branch:** `spec`
**Aligns with:** [`docs/DESIGN.md`](docs/DESIGN.md) (product brief), [`docs/RULES-AND-POLICIES.md`](docs/RULES-AND-POLICIES.md) (rule catalog), [`docs/diagrams/architecture.png`](docs/diagrams/architecture.png) (published icon figure).

This document is the technical *how* behind [`requirements.md`](requirements.md). It does not restate the product brief; it specifies components, data model, interfaces, degrade/fail-safe paths, and over-claim controls, then hands ordered work to [`tasks.md`](tasks.md).

---

## 1. Architecture overview

The published, icon-based figure in [`docs/diagrams/architecture.png`](docs/diagrams/architecture.png) (source `docs/diagrams/architecture.py`, walkthrough `docs/diagrams/ARCHITECTURE-EXPLAINED.md`) is the official architecture diagram. This section mirrors it in words; it does **not** replace it with a box-only diagram. If the architecture changes, regenerate the PNG/SVG from the Python generator with the existing icon set.

Four lanes, left to right:

1. **Sources** — synthetic extracts for Customer, Product, Finance, HR across two country companies. `oss`: local CSV/Parquet in-repo (all four domains, including HR). `hybrid`: Finance optionally from Azure SQL, Product optionally from Azure Blob; HR always local.
2. **Contracts + quality gate** — ODCS v3.2.0 contracts declare critical elements and rules; dbt builds marts; Great Expectations + dbt tests run the `DQ-*` rules. Fail closed → quarantine + steward issue.
3. **Governance core** — catalog/glossary (OpenMetadata), lineage, classification tags, ownership/RACI, policies + RoPA + retention flags. Our code holds the operating model.
4. **Consumers** — KPI scorecard + PDF report; the `AI-FIT-01` label pack exported to the sibling AI platform (fixture consumer in this repo). Humans in the loop: Data Owner, Data Steward (Datenverantwortlicher), DPO.

Vendor boxes (Microsoft Purview, Collibra, SAP MDG) appear on the figure as optional/recommended buys, never as components we build.

```
sources ──▶ contracts + quality gate ──▶ governance core ──▶ consumers (scorecard / report / AI labels)
                     │                         │
                 fail closed               RoPA / retention flags
                     ▼                         ▼
             steward issue + cleanse      classification tags
```

---

## 2. Profiles and configuration

| Concern | `oss` (default, CI-guaranteed) | `hybrid` (optional, Phase 9) |
|---|---|---|
| Sources | local files, all domains | + Azure SQL (Finance), Azure Blob (Product); HR stays local |
| Catalog | OpenMetadata in Compose; recorded fixtures in CI | OpenMetadata + Microsoft catalog sync **mock** (live backend only if a usable account exists; default mock) |
| Quality | GE + dbt | same |
| Identity | local users / Keycloak | Entra ID group→owner/role mapping if group claims work; else local |
| Evidence | files + PDF | + optional Azure Monitor |

- Configuration is environment variables only, prefix `DG_`. Key vars: `DG_PROFILE`, `DG_CATALOG_BACKEND=mock|purview|fabric` (default `mock`), `DG_AZURE_SQL_*`, `DG_AZURE_STORAGE_*`, `DG_ENTRA_*`, `DG_AZURE_MONITOR_*`.
- No secrets committed; no subscription ID in README/PDF. Absent `DG_*` → adapters resolve to mocks and `make demo` still runs.

---

## 3. Repository layout (proposed)

```
.
├── Makefile                     # pull/bootstrap, demo, report, test, validate
├── docker-compose.yml           # OpenMetadata + deps for local demo (oss)
├── README.md                    # ~3-min skim
├── docs/
│   ├── DESIGN.md  CASE-STUDY.md  RULES-AND-POLICIES.md  HYBRID.md (Phase 9)
│   └── diagrams/                # published icon figures + architecture.py (do not replace with Mermaid)
├── requirements.md  design.md  tasks.md
├── data/
│   ├── raw/{customer,product,finance,hr}/   # synthetic dirty extracts, two companies
│   └── reference/finance_company_codes.csv  # cost-centre reference for DQ-FIN-001
├── contracts/                   # ODCS v3.2.0 YAML, one per domain product + reference lists
├── dbt/                         # domain marts, KPI datasets, lineage, dbt tests
├── quality/                     # Great Expectations suites + rule registry (DQ-* → check)
├── governance/
│   ├── glossary/                # terms EN + DE aliases
│   ├── raci/                    # ownership register (GOV-RACI-01)
│   ├── policies/                # POL-GDPR-01..06 (IDs + own-words titles)
│   ├── ropa/                    # Customer + HR RoPA (Art. 30(1) field set)
│   └── classification/          # tag set + assignments
├── workflow/                    # steward issue / cleanse engine
├── labels/                      # AI-FIT-01 computation + label-pack schema + exporter
├── fixtures/ai_gateway/         # deny/ask/allow consumer standing in for sibling platform
├── adapters/                    # azure_sql, azure_blob, entra, azure_monitor, catalog_sync (+ mocks)
├── report/                      # PDF renderer (fail-closed)
├── eval/results/                # committed runs: scorecard, coverage, demo duration (ts + SHA)
├── schemas/                     # JSON schemas: label pack, RoPA, RACI, run file
└── tests/                       # per-rule, schema, workflow, label, adapter-absent
```

---

## 4. Data model

### 4.1 Domains and critical elements (starter set)
- **Customer:** `customer_id` (`master.customer`), `email` (`pii.contact`), `vat_id`, country company.
- **Product:** `product_id`, `name`, `status`, `unit_of_measure`.
- **Finance:** `cost_centre_id` (+ company-code reference list), vendor/invoice totals for the reconciliation defect, `confidential.finance`.
- **HR (local-only):** employee master with `status`, `effective_from`, `effective_to`, `last_verified_on`, fields tagged `pii.hr`.

### 4.2 ODCS contracts
- `apiVersion: v3.2.0`, `kind: DataContract`, media type `application/odcs+yaml;version=3.2.0`.
- One contract per domain product + reference lists. Custom properties carry lab policy IDs, classification, owner, steward, retention class, and the per-country VAT pattern (a documented contract parameter, not an official VAT spec).
- Validated against the official ODCS v3.2.0 JSON schema; validation failure fails the step.

### 4.3 Classification tags
`pii.contact`, `pii.hr`, `confidential.finance`, `master.customer`, `fit_for_ai`, `not_fit_for_ai` — applied in OpenMetadata and mirrored in `governance/classification/` so CI can check without a live catalog.

### 4.4 Label pack (`AI-FIT-01`)
JSON/YAML records against `schemas/label-pack.schema.json`:
`{asset_id, field, classification, owner, steward, fit_for_ai, policy_version}` (+ run metadata). Versioned; `fit_for_ai` true only when §6 gate passes.

### 4.5 RoPA and run files
- RoPA: Customer + HR, Art. 30(1) field set, schema-validated.
- Run file (`eval/results/*.json`): metrics + `generated_at` (UTC) + `git_sha`. README/report read numbers only from these.

---

## 5. Quality gate design

- **Rule registry** maps each catalog ID to its check implementation, severity and on-fail action. GE suites cover value/format/uniqueness checks; dbt tests cover relational/reference checks (e.g. `DQ-FIN-001` against the company-code reference) and the finance reconciliation.
- **Fail-closed executor:** on any failure, the row is quarantined or the gate blocks per the catalogued action, a steward issue is opened, and (for `DQ-CUS-001`/`DQ-HR-001`) `fit_for_ai` is withheld. No path lets a failure pass silently.
- **Severity → blast radius:** `critical` (`DQ-CUS-002`, `DQ-FIN-001`) blocks the data product / mart row and dependent KPI/export; `high` quarantines the row and holds it out of the product.
- **Scorecard:** completeness, uniqueness, consistency, currentness + cross-domain key matches. Renders `TARGET`/`TO BE MEASURED` until a committed run exists.

| Rule | Engine | Severity | On-fail (summary) |
|---|---|---|---|
| DQ-CUS-001 | GE | high | quarantine, issue, no export, no `fit_for_ai` |
| DQ-CUS-002 | GE/dbt | critical | block product + campaign export, issue |
| DQ-CUS-003 | GE | high | fail row, issue, do not use VAT ID |
| DQ-PRD-001 | GE | high | hold out of product, issue |
| DQ-FIN-001 | dbt | critical | block mart row, issue, no KPI |
| DQ-HR-001 | GE/dbt | high | quarantine, issue, `not_fit_for_ai`, no export |

---

## 6. `AI-FIT-01` gate and export

`fit_for_ai = true` **iff** all hold: named owner + steward present; classification assigned; relevant `DQ-*` rules passed; applicable `POL-GDPR-01/02/04/06` satisfied; lineage recorded. Otherwise `not_fit_for_ai`.

- Exporter writes a versioned label pack validated against the schema.
- Fixture consumer (`fixtures/ai_gateway/`) replays DESIGN.md §9: requests touching `pii.contact`/`pii.hr`/`confidential.finance`/`not_fit_for_ai` → `deny`/`ask`; an approved non-PII KPI aggregate → `allow`. This repo computes labels only; the PEP and allow/deny policy live in the sibling repos and are never imported or edited here.

---

## 7. Governance core

- **Catalog:** OpenMetadata (Compose) for the demo; CI uses recorded fixtures (`governance/` mirrors) so the pipeline stays light and offline.
- **Glossary:** EN terms + DE aliases; each critical element links definition + technical metadata + classification + contract + rule (`GOV-META-01`).
- **RACI (`GOV-RACI-01`):** YAML register; every critical element resolves a Data Owner and a Data Steward (Datenverantwortlicher). The steward is explicitly not the GDPR Art. 4(7) controller; the DPO is a separate function.
- **MDM (`GOV-MDM-01`):** documented system-of-record and create-change-approve path for `customer_id`/`product_id`; SAP MDG referenced as a buy option, never built.
- **Policies / RoPA / retention:** `POL-GDPR-01…06` as checks/workflows; Customer + HR RoPA; retention reached → flag only, never production deletion.

---

## 8. Steward issue / cleanse workflow

State machine: `open → decided (cleanse | exception) → re-run → closed`. An issue records rule ID, record key, severity, timestamp, decision and outcome. A recorded exception is explicit and auditable. The demo drives one failed record end-to-end and records the issue-cycle process metric (not a production SLA).

---

## 9. Hybrid adapters (Phase 9)

- **Interface-first:** each adapter has a mock (required) and an optional live backend; selection by `DG_*` env. Missing creds → mock, clean degrade, `make demo` still runs.
- **Azure SQL (Finance):** free General Purpose serverless, Germany West Central, auto-pause on idle and on free-limit, never "continue with charges".
- **Azure Blob (Product):** StorageV2 Hot LRS, smallest account, short-lived container.
- **Entra ID:** group→owner/steward/role mapping; mock if app registration / group claims are unavailable.
- **Azure Monitor:** optional evidence sink, smallest workspace, shortest retention.
- **Catalog sync:** publishes the same terms/assets/tags; backends `mock` (default/required), `purview`/`fabric` only if a usable account exists — **not assumed**. See the Purview reality check below.
- **Rules:** region Germany West Central only; portal-only creation (Azure CLI device login blocked); create-test-delete same session; HR never to Azure; no Fabric trial / paid F SKU; subscription ID never published; secrets env-only.

### 9.1 Purview / Fabric reality check
Microsoft Purview Data Governance is retiring (announced 12 Nov 2026; new accounts may be uncreatable; maintenance through 12 Nov 2027). Successor is the Fabric OneLake catalog (capacity-billed; student/trial availability unverified). Default assumption: no live Microsoft catalog; the adapter stays mocked and the report says so. A hybrid session is still a success when Azure SQL and/or Blob (and optionally Entra/Monitor) run live with the catalog mocked.

---

## 10. CI, demo, report

- **CI (`oss` only, every PR):** ODCS schema validation; dbt tests; GE (or unit equivalent exercising the same rules); workflow tests; label-export tests; adapter-absent tests; scorecard/coverage report printing `TARGET` or last committed figures. No live cloud, no live OpenMetadata required.
- **`make pull` / `make bootstrap`:** one-time image pull, outside the demo clock.
- **`make demo`:** DESIGN.md §9 script on `oss`, under 15 minutes after pull; writes a duration run file.
- **`make report`:** PDF pack (brief, diagnosis, options, solution, results, roadmap); **fails closed** if a required field is missing or a results number lacks a committed run file. Links the published icon figure.

---

## 11. Fail-safe and degrade paths

| Situation | Behaviour |
|---|---|
| Quality rule fails | fail closed: quarantine/block per severity + steward issue; never silent skip |
| No committed run file | scorecard/README show `TARGET`/`TO BE MEASURED` |
| Report field missing / number unsourced | `make report` errors, no PDF |
| `DG_*` creds absent | adapters → mocks; `make demo` still runs |
| Live Microsoft catalog unavailable | catalog adapter stays mocked; report states it plainly |
| OpenMetadata too heavy for CI | CI uses recorded fixtures; live OpenMetadata only in local demo |

---

## 12. Threat and over-claim notes

- **Privacy:** synthetic data only; HR local-only (test asserts no HR→Azure binding); env-only secrets; no subscription ID in public artefacts; no prompt bodies stored.
- **Scope boundary:** no PEP here; no allow/deny decision; sibling repos never imported or edited (test asserts no sibling paths written).
- **Over-claim control:** SAP MDG / Collibra / Informatica / Purview / Fabric are buy-vs-build docs; CV wording per DESIGN.md §11; mappings illustrative; no copied statutory/standard text (ID + own-words title only; a doc lint guards this).
- **Reproducibility:** every published number traces to a committed `eval/results/` file with UTC timestamp + git SHA.

---

## 13. Testing strategy

- **Contract/schema:** ODCS v3.2.0 validation; label-pack, RoPA, RACI, run-file schema validation.
- **Per-rule:** one test per `DQ-*` asserting pass/fail + exact severity + on-fail action.
- **Workflow:** fail → issue → decision → cleanse → re-run → pass; exception path auditable.
- **Label/fixture:** `AI-FIT-01` gate logic; §9 deny/ask/allow outcomes; no sibling-repo writes.
- **Adapter-absent:** all `hybrid` adapters resolve to mocks with no `DG_*`; HR has no Azure binding; catalog defaults to mock.
- **Report:** fail-closed on missing field / unsourced number; published diagram present and referenced.
