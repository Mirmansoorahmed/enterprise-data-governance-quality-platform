# Requirements — Enterprise Data Governance & Quality Platform

**Repo:** `enterprise-data-governance-quality-platform` · **Branch:** `spec` · **Status:** spec for review, no implementation yet.
**Fiction:** consultancy *Northwind Advisory*, client *Tarsfeld Group GmbH* (synthetic, four domains: Customer, Product, Finance, HR).
**Source of truth:** [`docs/DESIGN.md`](docs/DESIGN.md) (product brief), [`docs/RULES-AND-POLICIES.md`](docs/RULES-AND-POLICIES.md) (rule catalog), [`docs/CASE-STUDY.md`](docs/CASE-STUDY.md) (narrative only).

This document is the *what* and the *acceptance criteria*. The *how* is in [`design.md`](design.md); the ordered work is in [`tasks.md`](tasks.md).

---

## 0. Conventions

- **EARS-style acceptance criteria.** "WHEN … THE SYSTEM SHALL …" / "IF … THEN …".
- **Profiles.** `oss` is the default and the only profile CI guarantees. `hybrid` is optional, feature-flagged, env-only (`DG_*`), and mocked in tests.
- **Fail closed.** A failed quality rule, a missing required report field, or a results number with no committed run file must stop the relevant step, never pass silently.
- **No invented numbers.** Any metric in README / report / case study must trace to a committed run file carrying a UTC timestamp and git SHA; otherwise it reads `TARGET` or `TO BE MEASURED`.
- **Rule IDs are canonical.** `DQ-CUS-001/002/003`, `DQ-PRD-001`, `DQ-FIN-001`, `DQ-HR-001`, `POL-GDPR-01…06`, `GOV-RACI-01`, `GOV-META-01`, `GOV-MDM-01`, `AI-FIT-01`. Do not add, drop, or renumber rules; do not invent statutory clause numbers.

### Client-approved defaults (locked)
Catalog adapter + mock only (no live Purview/Fabric); HR data stays local; no Fabric trial; Finance mapped to Azure SQL and Product to Blob in `hybrid`; OpenMetadata live locally with recorded fixtures in CI; case study in English.

---

## 1. Actors

| Actor | Role |
|---|---|
| Data Owner | RACI-accountable for a domain / critical element. |
| Data Steward (*Datenverantwortlicher*) | Runs the issue / cleanse workflow. Not the GDPR Art. 4(7) controller. |
| DPO | Owns RoPA, minimisation and retention review. Statutory function, separate from the steward. |
| Consultant / platform operator | Runs `make demo`, `make report`, and (with explicit go) the hybrid portal session. |
| AI platform (sibling) | Consumes the exported label pack. This repo never decides allow/ask/deny. |
| CI | Runs the `oss` pipeline on every PR. |

---

## 2. Functional requirements

### R1 — Synthetic data and ODCS contracts
**User story:** As the consultant, I want synthetic, intentionally dirty multi-domain extracts under versioned data contracts, so the demo shows real governance problems honestly.

- R1.1 WHEN the repo is checked out THE SYSTEM SHALL provide synthetic extracts for all four domains (Customer, Product, Finance, HR) across two country companies (German HQ + one other), with no real personal or company data.
- R1.2 THE SYSTEM SHALL seed defects that exercise every `DQ-*` rule: mismatched/duplicate customer keys across companies, missing product mandatory attributes, a finance total that does not reconcile and an inactive/invalid `cost_centre_id`, invalid/missing customer email, VAT values that violate the contract pattern, and HR rows outside the currentness window or missing classification.
- R1.3 THE SYSTEM SHALL provide one ODCS **v3.2.0** YAML contract per domain data product, plus reference lists (at least the Finance company-code / cost-centre reference) where a rule needs one. Each contract SHALL use `apiVersion: v3.2.0`, `kind: DataContract`, and carry custom properties for lab policy IDs, classification, owner, steward and retention class.
- R1.4 WHEN a contract is validated THE SYSTEM SHALL check it against the official ODCS v3.2.0 schema and FAIL the step on any schema violation.
- R1.5 THE SYSTEM SHALL NOT configure the HR domain for any Azure source; HR extracts stay local in both profiles.
- **Acceptance:** schema validation passes for all contracts; the dirty extracts reproducibly trigger each `DQ-*` rule; a test asserts HR has no Azure source binding.

### R2 — dbt marts and lineage
**User story:** As a Data Owner, I want one documented KPI dataset per domain built by dbt, so lineage from source extract to scorecard is visible.

- R2.1 THE SYSTEM SHALL build domain marts with dbt for all four domains, at least one KPI dataset per domain, path source → mart → scorecard.
- R2.2 THE SYSTEM SHALL expose lineage for each declared KPI dataset to its source extract(s), recorded so it can be shown in the catalog and the report.
- R2.3 WHEN a Finance row fails `DQ-FIN-001` THE SYSTEM SHALL block that row from the finance mart load and SHALL NOT publish the dependent KPI.
- **Acceptance:** lineage coverage is binary yes on the declared KPI datasets; a test confirms a `DQ-FIN-001` failure holds back the row and the KPI.

### R3 — Quality gate and scorecard
**User story:** As a Data Steward, I want every catalogued rule enforced with its severity and on-fail action, so a failure always produces a traceable outcome.

- R3.1 THE SYSTEM SHALL implement every `DQ-*` rule via Great Expectations and/or dbt tests with the severity and action-on-fail exactly as in [`docs/RULES-AND-POLICIES.md`](docs/RULES-AND-POLICIES.md):
  - `DQ-CUS-001` (high): email present + valid against the contract pattern → fail gate, quarantine, steward issue, no export, no `fit_for_ai`.
  - `DQ-CUS-002` (critical): `customer_id` present + unique across both companies → fail gate, block customer product + campaign export, steward issue.
  - `DQ-CUS-003` (high): when `vat_id` present, country code + block matches the contract per-country pattern → fail the row, steward issue, do not use the VAT ID.
  - `DQ-PRD-001` (high): `product_id`, `name`, `status`, `unit_of_measure` present → fail gate, hold out of product product, steward issue.
  - `DQ-FIN-001` (critical): `cost_centre_id` exists and is active in the company-code reference → fail gate, block mart row, steward issue, do not publish KPI.
  - `DQ-HR-001` (high): `status`, `effective_from`, `last_verified_on` within currentness window, leavers have `effective_to` → fail gate, quarantine, steward issue, `not_fit_for_ai`, no export.
- R3.2 WHEN any rule fails THE SYSTEM SHALL fail closed (block or quarantine) and open a steward issue; a silent skip is a defect.
- R3.3 THE SYSTEM SHALL produce a KPI scorecard covering completeness, uniqueness, consistency and currentness, plus cross-domain key-match checks.
- R3.4 WHEN no committed run file exists THE SYSTEM SHALL render scorecard cells as `TARGET` or `TO BE MEASURED`, never as an invented number.
- R3.5 THE SYSTEM SHALL NOT treat VAT national patterns as official; the per-country pattern is a documented contract parameter for the synthetic set.
- **Acceptance:** a test per rule asserts correct pass/fail plus the exact on-fail action and severity; the scorecard renders placeholders until a run file is present.

### R4 — Catalog, glossary, ownership
**User story:** As a Data Owner, I want a glossary and an ownership register tied to contracts and rules, so every critical element has a definition and named accountability.

- R4.1 THE SYSTEM SHALL run OpenMetadata locally (Docker Compose) for the demo, holding glossary terms (English with German aliases), tags and lineage; CI MAY use recorded catalog fixtures instead of a live OpenMetadata.
- R4.2 THE SYSTEM SHALL implement `GOV-RACI-01`: every declared critical element has a named Data Owner and Data Steward.
- R4.3 THE SYSTEM SHALL implement `GOV-META-01`: each critical element links glossary definition + technical metadata + classification + its contract and its quality rule.
- R4.4 THE SYSTEM SHALL implement `GOV-MDM-01`: a documented system-of-record and create-change-approve path for `customer_id` and `product_id` (synthetic only; SAP MDG referenced as a buy option, never implemented).
- R4.5 THE SYSTEM SHALL label the steward role bilingually as "Data Steward (Datenverantwortlicher)" and SHALL NOT equate the steward with the GDPR controller.
- **Acceptance:** a test asserts every declared critical element resolves an owner, steward, definition, classification, contract link and rule link; a test confirms CI needs no live OpenMetadata.

### R5 — Classification, RoPA, retention, access
**User story:** As the DPO, I want classification tags, a short RoPA and retention flags, so privacy obligations are visible without a false compliance claim.

- R5.1 THE SYSTEM SHALL apply the tag set: `pii.contact`, `pii.hr`, `confidential.finance`, `master.customer`, `fit_for_ai`, `not_fit_for_ai`.
- R5.2 THE SYSTEM SHALL implement policies `POL-GDPR-01` through `POL-GDPR-06`, each mapped to a check or workflow as catalogued (minimisation; accuracy; storage limitation/retention flags; RoPA completeness; protection by design; security of processing & access).
- R5.3 THE SYSTEM SHALL maintain a short electronic RoPA for Customer and HR with the Art. 30(1) field set.
- R5.4 WHEN a retention threshold is reached THE SYSTEM SHALL set a retention **flag** and SHALL NOT perform any production deletion.
- R5.5 THE SYSTEM SHALL keep classification/policy mappings illustrative; no copied statutory or standard text, no conformity claim.
- **Acceptance:** schema-valid RoPA with required fields; tests confirm retention only flags; a lint/test fails if a policy doc copies statutory text (ID + short own-words title only).

### R6 — Steward issue / cleanse workflow
**User story:** As a Data Steward, I want a failed row to become an issue I can resolve and re-check, so the business–IT interface is demonstrable.

- R6.1 WHEN a rule fails THE SYSTEM SHALL create a steward issue capturing the rule ID, record key, severity and timestamp.
- R6.2 THE SYSTEM SHALL let the steward record a decision (cleanse or exception) and apply a documented cleanse, then re-run the rule.
- R6.3 WHEN the cleanse resolves the failure THE SYSTEM SHALL close the issue and allow the record forward; IF an exception is recorded THEN the exception SHALL be explicit and auditable.
- **Acceptance:** an end-to-end test drives fail → issue → decision → cleanse → re-run → pass, and records an issue-cycle process metric.

### R7 — AI label export (`AI-FIT-01`)
**User story:** As the sibling AI platform, I want a versioned label pack, so I can reason about data without this repo deciding access.

- R7.1 THE SYSTEM SHALL compute `fit_for_ai` only when ownership, classification, the relevant quality-gate rules, applicable `POL-GDPR-01/02/04/06`, and lineage are all in place; otherwise `not_fit_for_ai`.
- R7.2 THE SYSTEM SHALL publish a versioned label pack with at least `{asset_id, field, classification, owner, steward, fit_for_ai, policy_version}` against a published schema.
- R7.3 THE SYSTEM SHALL provide a fixture consumer standing in for AI Compliance Automation / the gateway that returns `deny`/`ask` for `pii.contact`, `pii.hr`, `confidential.finance` or `not_fit_for_ai` requests, and `allow` for an already-approved non-PII KPI aggregate (DESIGN.md §9).
- R7.4 THE SYSTEM SHALL NOT implement a PEP, store prompt bodies, or edit any sibling repo.
- **Acceptance:** schema-valid label pack; fixture tests assert the §9 deny/ask/allow outcomes; a test asserts no sibling-repo paths are written.

### R8 — Demo, report, evidence
**User story:** As a hiring manager, I want a short demo and a PDF pack, so I can see the operating model quickly and honestly.

- R8.1 THE SYSTEM SHALL provide `make pull` / `make bootstrap` as a one-time image pull outside the demo clock.
- R8.2 WHEN `make demo` runs on `oss` after images are pulled THE SYSTEM SHALL execute the DESIGN.md §9 script and SHALL complete in under 15 minutes.
- R8.3 WHEN `make report` runs THE SYSTEM SHALL produce a PDF case-study pack (brief, diagnosis, options, solution, results, roadmap) and SHALL fail closed if a required field is missing or a results number has no committed run file.
- R8.4 THE SYSTEM SHALL keep the icon-based `docs/diagrams/architecture.png`/`.svg` as the published figures; IF a figure changes THEN it SHALL be regenerated from `docs/diagrams/architecture.py` with the existing icon set, never replaced by a box-only Mermaid diagram.
- R8.5 THE SYSTEM SHALL persist runs under `eval/results/` with UTC timestamp and git SHA; README figures read only from committed run files.
- R8.6 THE SYSTEM SHALL keep the README skimmable in ~3 minutes: problem → icon figure → how to run (both profiles) → results table (when measured) → limitations.
- **Acceptance:** a timed `make demo` run writes a duration file; the report renderer errors on a missing field or an unsourced number; a test asserts the published diagram files are present and referenced.

### R9 — Hybrid profile (optional, Phase 9)
**User story:** As the consultant, I want optional Azure-first adapters that degrade cleanly, so a Microsoft estate can be shown without making CI depend on it.

- R9.1 THE SYSTEM SHALL implement feature-flagged, env-only (`DG_*`) adapters: Azure SQL Database (Finance), Azure Blob Storage (Product), Entra ID group-to-owner/role mapping, optional Azure Monitor, and a Microsoft catalog sync interface with a **required mock backend**.
- R9.2 WHEN Azure credentials are absent THE SYSTEM SHALL degrade to mocks and still run `make demo`; tests SHALL exercise the adapter-absent path.
- R9.3 THE SYSTEM SHALL restrict any Azure resource to region **Germany West Central**, smallest/free tiers, portal-only creation (Azure CLI device login is blocked), auto-pause on the SQL free offer, never "continue with charges", create-test-delete in one session.
- R9.4 THE SYSTEM SHALL keep the catalog adapter mocked by default (no live Purview/Fabric), SHALL NOT start a Fabric trial or a paid Fabric F SKU, and SHALL NOT load HR to Azure.
- R9.5 THE SYSTEM SHALL provide `docs/HYBRID.md` with portal steps, env vars, cost notes, a teardown checklist, and a results section filled only after a real session (timestamp + git SHA, live vs mock separated). The subscription ID SHALL NOT appear in README or the PDF; secrets SHALL NOT be committed.
- **Acceptance:** adapter-absent tests pass with no `DG_*` set; a test asserts HR has no Azure binding and the catalog adapter defaults to mock; `HYBRID.md` exists with the required sections and no secrets.

---

## 3. Non-functional requirements

- **NFR1 Portability:** `oss` runs with no cloud account on a small sample; CI passes on `oss` only.
- **NFR2 Performance:** `make demo` under 15 minutes after image pull; `make pull`/`make bootstrap` excluded from that clock.
- **NFR3 Security/privacy:** synthetic data only; HR local-only; env-only secrets (`DG_*`); no committed secrets; no subscription ID in public artefacts.
- **NFR4 Reproducibility:** every published number sourced from a committed `eval/results/` run with timestamp + git SHA.
- **NFR5 Traceability:** every automated check maps to a catalog ID; mappings illustrative, no copied legal/standard text.
- **NFR6 Honesty / no over-claim:** SAP MDG, Collibra, Informatica, Purview, Fabric are buy-vs-build docs, not implementations; CV wording per DESIGN.md §11.
- **NFR7 Testability:** tests required for contract/schema validation, each quality rule, policy/workflow gates, label export, and adapter-absent paths.
- **NFR8 Commit hygiene:** small, labelled commits (e.g. `phase-3: add DQ-FIN-001`); no `Co-authored-by`, no AI attribution.
- **NFR9 Docs:** README ~3-minute skim; published icon diagrams kept and regenerated from the Python generator only.

---

## 4. Out of scope (v1)

Implementing SAP MDG / S/4, Salesforce, Workday, or any real CRM/ERP/HRIS; production Purview/Fabric rollout or a paid Fabric F SKU; replacing the gateway or rewriting AI Compliance Automation; a PEP in this repo; legal sign-off, works agreement, or any GDPR/ISO/EU AI Act conformity claim; production HA, multi-region cut-over, or a second cloud; any real customer or employee data.

---

## 5. Traceability summary

| Requirement | Catalog IDs | Phase (tasks.md) |
|---|---|---|
| R1 | ODCS contracts | 1 |
| R2 | KPI datasets, lineage | 2 |
| R3 | `DQ-CUS-001/002/003`, `DQ-PRD-001`, `DQ-FIN-001`, `DQ-HR-001` | 3 |
| R4 | `GOV-RACI-01`, `GOV-META-01`, `GOV-MDM-01` | 4 |
| R5 | `POL-GDPR-01…06`, tag set | 5 |
| R6 | steward workflow | 6 |
| R7 | `AI-FIT-01`, label schema | 7 |
| R8 | demo/report/eval | 0, 8 |
| R9 | `DG_*` adapters | 9 |
