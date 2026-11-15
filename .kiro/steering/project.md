# Steering — enterprise-data-governance-quality-platform

## Purpose
Portfolio project: **Enterprise Data Governance & Quality Platform** (`enterprise-data-governance-quality-platform`). A consulting case study that stands up a data-governance operating model — catalog, quality rules, ownership/stewardship, master data, lineage, GDPR (RoPA, retention, PII classification), and data contracts — on synthetic multi-domain data.

Demo consultancy: **Northwind Advisory**. Demo client: **Tarsfeld Group GmbH** (fictional mid-to-large European group, about 6,000 employees, headquarters in Germany, operating companies in more than one country). Domains: Customer, Product, Finance, HR. Industry-neutral. Not a real firm. Not Vaillant or any other real employer. Not NordPay. Not a SAP / sales-only story.

Sits beside the AI Governance Platform. This repo **publishes** classification, ownership and `fit_for_ai` / `not_fit_for_ai` labels. It does **not** make allow / ask / deny decisions and must not edit `ai-compliance-automation`, the Agent Access Governance Gateway, or `agent-trust-gateway`.

## Stack (hybrid, portable by default; Azure first where realistic)
- **Default profile `oss` (CI must pass with this only):** Python, Docker Compose, OpenMetadata, Great Expectations, dbt, Open Data Contract Standard (ODCS) v3.2.0 YAML, our operating-model code (policies, RACI, stewardship workflow, KPI scorecard, RoPA, classification, label export), local users or Keycloak, file + PDF evidence. Optional Streamlit or Grafana board. Must run with no cloud account and a small synthetic sample.
- **Optional profile `hybrid`:** same core, plus feature-flagged, env-only adapters (see DESIGN.md Azure section): Azure SQL Database (free serverless offer) and/or Azure Blob Storage as sources; Microsoft Entra ID for group-to-owner/role mapping; optional Azure Monitor; a Microsoft catalog sync adapter (Purview Data Governance / Fabric OneLake catalog) that must degrade to a mock when the service cannot be created. Adapters degrade cleanly when credentials are missing.
- Region for any Azure resource: **Germany West Central only**. Portal-only creation (Azure CLI device login is blocked). Smallest or free tiers, create-test-delete. Budget alert already exists.

## Hard constraints
- **Synthetic data only.** Fictional firms: Northwind Advisory and Tarsfeld Group GmbH. No real client data. Even synthetic HR PII stays local; do not upload the HR domain to Azure.
- **No employer branding** (no Telekom, Magenta, PwC, or other real employer names) on demos, READMEs, or reports. No real company as the client.
- **No AI attribution** and **no `Co-authored-by`** (or similar) on commits. Commits are small and labelled (for example `phase-3: add DQ-FIN-001`).
- **Never invent metrics.** Every number in README / report / case study / CV draft must come from a **committed eval or quality run** with **timestamp + git SHA**. Until then write "TO BE MEASURED" or "TARGET". No invented hybrid numbers.
- **Do not copy legal or standard text.** Article, clause or knowledge-area IDs plus short titles in our own words. Mappings are illustrative, not a conformity, certification, or compliance claim. There is no ISO 4001 in this design. ISO 9001 and ISO/IEC 38505-1 are context only, not field checks.
- **SAP MDG / S/4, Collibra, Informatica, Alation, Ataccama** are buy-versus-build documentation only, not implementations. A thin S/4-style file-format stub is the most that is allowed, and it must never be described as SAP experience.
- Tests required for contract/schema validation, quality rules, policy/workflow gates, label export, and adapter-absent paths.
- README must be skimmable in ~3 minutes: problem → icon architecture figure → how to run (`make demo`, both profiles) → results table (when measured) → limitations.
- Full `make demo` (oss) must run in **under 15 minutes** after images are already pulled. `make pull` / `make bootstrap` is a one-time step outside that clock.

## Docs Mir will place for you
- `docs/DESIGN.md` (product design)
- `docs/CASE-STUDY.md` (consulting narrative; do not invent results)
- `docs/RULES-AND-POLICIES.md` (source-cited rule catalog)
- `docs/diagrams/architecture.png` (icon-based published figure, plus svg, explained figure, generator, icons)
- `README.md`

## Out of scope (v1)
- Production HA, multi-region cut-over, or a second-cloud implementation
- Implementing SAP MDG, SAP S/4, Salesforce, Workday, or any real CRM / ERP / HRIS
- Production Purview or Fabric rollout, or buying a paid Fabric F SKU
- Replacing the gateway or rewriting AI Compliance Automation
- Legal sign-off, a works agreement, or a claim of GDPR / ISO / EU AI Act conformity
- Real customer or employee data
