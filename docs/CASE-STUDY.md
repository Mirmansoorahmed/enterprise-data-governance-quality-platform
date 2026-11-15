# Case study: Enterprise Data Governance & Quality Platform for Tarsfeld Group GmbH

**Portfolio case study** · prepared for Mir Mansoor Ahmed
**Role in the fiction:** consultant at *Northwind Advisory*
**Client in the fiction:** *Tarsfeld Group GmbH* — a diversified mid-to-large European group, about 6,000 employees, headquarters in Germany, operating companies in more than one country. Critical data sits in four domains: Customer, Product, Finance and HR. Not a real firm. Not Vaillant, not any other real employer, and not NordPay.
**Date:** 15 November 2026 (Europe/Berlin)
**Status:** proposed engagement and lab design. This is not a completed client delivery, not legal advice, and not a conformity assessment. No results have been measured yet.

Technical design: [`DESIGN.md`](DESIGN.md). Source-cited rules: [`RULES-AND-POLICIES.md`](RULES-AND-POLICIES.md). Icon architecture figure: [`diagrams/architecture.png`](diagrams/architecture.png).

---

## Rules (do not delete from this case study)

- Never invent metrics, headcount of a real employer, repo stars, or outcomes. If it was not measured, write **TO BE MEASURED** (or "not measured") and leave the cell empty of numbers.
- Never copy text from ISO, the GDPR, the EU AI Act, or other standards. Use clause or article IDs plus a short title in your own words.
- Synthetic data and fictional names only. No real client data, no home address, no personal phone numbers. Even synthetic HR PII stays local in the lab and is not uploaded to Azure.
- Cloud and vendor choices must be honest: adapters and feature flags, a path that runs without paid APIs, and unverified account limits listed as TODOs to check.
- Commits in the real repo: no `Co-authored-by`, no AI attribution.
- No real employer brand (no Telekom, Magenta, PwC, or others) and no real company presented as the client.

---

## 1. Client brief

Tarsfeld Group GmbH is a fictional diversified European group. Critical data is not in one commercial domain. It sits in Customer (CRM extracts: party, contact, account), Product (product and material master, hierarchy), Finance (vendor, invoice, cost centre), and HR (employee master). HR is treated as the most sensitive domain.

The brief, in the voice of a fictional CDO and a fictional DPO:

- The same customer and product identifiers do not match across country companies and systems. Finance cannot reconcile vendor and invoice totals to the operational reports. HR and customer contact data are not consistently classified.
- A data-platform programme is planned. Nobody can show which fields are critical, who owns them, which quality rules apply, or which records may be used by an assistant.
- The works council and the DPO care about employee and customer contact data. A record of processing is incomplete.
- Assistants and coding agents are starting to be used in operations and finance. There is no rule that data going into those tools must already be classified and owned.

Northwind Advisory is asked to stand up a **data-governance operating model** for the critical data elements of all four domains, and to show how that model would sit on top of the tools a firm like this would actually buy, without locking the demo to a single vendor cloud.

---

## 2. Problem diagnosis

### As-is

- Four domains, no shared definitions, weak ownership, and quality rules that live in people’s heads.
- No catalog of record, incomplete classification, and no path from a failed check to a steward decision.
- A RoPA for customer and employee processing is incomplete or missing.
- AI use is starting without a label for “fit for AI.”
- If the group already licenses Microsoft 365 or Azure, those licences are not yet used as a governed source or catalog for these domains. If some country companies run SAP, there is no honest MDM recommendation written down — only an assumption that “the ERP will sort it out.”

### Risks

- Decisions, financial reports and customer campaigns run on mismatched keys and incomplete records.
- Personal data is exported or fed to an assistant without a purpose, a retention class, or an access rule.
- An audit or a DPO review finds policies on slides and no evidence pack.
- A later high-risk AI use case would inherit unowned, unclassified, unmeasured data (EU AI Act Art. 10 is about data and data governance — this lab does not classify the client’s systems, but the supply-side gap is already visible).
- Buying a catalog or SAP MDG without an operating model leaves the same ownership and quality gaps in a more expensive tool.

### Legal and organisational requirements (illustrative, not a classification)

- **GDPR:** Art. 5(1)(c) data minimisation; Art. 5(1)(d) accuracy and kept up to date; Art. 5(1)(e) storage limitation; Art. 25 protection by design and by default; Art. 30 record of processing; Art. 32 security of processing. The Art. 4(7) controller is the organisation, not an individual steward.
- **ISO 8000 and ISO/IEC 25012** as the quality-measurement and quality-model references for the gate (public abstracts and public characteristic names only; not a certification claim).
- **DAMA-DMBOK2R** knowledge areas for governance and stewardship, metadata, quality, and reference / master data (a body of knowledge, not a regulation).
- **EU AI Act Art. 10** (data and data governance) as the reason a `fit_for_ai` label exists. This platform is not itself a high-risk AI system, and this is not a conformity assessment.
- Because employee data is in scope, **Betriebsrat** co-determination under § 87 Abs. 1 Nr. 6 BetrVG is a client legal and social step, not something this lab “implements.” The technical default is synthetic data, local-only HR, and no production deletion.

### Stakeholders

| Role | Interest |
|---|---|
| CDO / data-platform lead | Shared definitions, ownership, a path to trusted data products |
| Domain Data Owners and Data Stewards (Datenverantwortliche) | Clear accountability and a usable issue / cleanse path |
| DPO / Legal | RoPA, minimisation, retention, no fake compliance claim |
| Betriebsrat | Purpose limitation on employee data, visibility of what is logged and classified |
| Finance and operations leads | Reconcilable keys and KPIs they can trust |
| CISO / AI platform owners | Labels that an assistant gateway can actually consume |
| Works / country-company IT | Something that can sit on Microsoft or run open source, and does not pretend to be SAP MDG |

---

## 3. Options and decision

Three options were compared. The detailed Buy vs. Build table is in [`DESIGN.md` §7](DESIGN.md).

**A. Buy only.** Adopt Microsoft Purview or, after the 12 November 2026 Purview Data Governance retirement, the Fabric OneLake catalog; or buy Collibra / Informatica / Alation; and buy SAP MDG if master-data create-change-approve is the pain in an SAP landscape. Strength: uses tools the market already names, and a vendor holds the product risk. Weakness: a catalog licence does not, by itself, write quality rules, a RACI, a RoPA, an issue workflow, or an AI-fit label. New Purview governance accounts may no longer be creatable. Fabric capacity is a cost and is unverified on a student or many mid-market tenants. The lab would have nothing honest to show if the Microsoft path is blocked.

**B. Build only, open source.** OpenMetadata, Great Expectations, dbt, ODCS contracts, our register and workflows, local files only. Strength: portable, reproducible, no student-account or vendor-quota risk. Weakness: ignores Azure and Entra estates many DACH clients already have; weaker story for a solutions-architect audience that expects a hybrid recommendation.

**C. Hybrid (recommended).** Keep the operating model — policies, RACI, stewardship workflow, quality rule pack, KPI scorecard, RoPA, classification and the AI label export — as our code, in Git, runnable fully open source. Buy or reuse commodity pieces behind adapters, with **Azure first where that is realistic**: Azure SQL Database and Azure Blob Storage as sources, Entra ID for group-to-owner mapping, optional Azure Monitor, and a Microsoft catalog sync **if** an account can actually be created. Recommend SAP MDG (or an equivalent hub) as a *buy* when MDM workflow is the client pain; do not clone it in the lab.

**Decision: C.** It matches how a consultant would actually land this at a Microsoft-leaning European group, without making the demo or CI depend on Azure being available. The lab account is **Azure for Students**, **USD $90** credit, expiry **7 November 2027**, **IU tenant**. Only **Germany West Central** is allowed. Azure CLI device login is blocked; the portal works. A budget alert already exists. Purview Data Governance retirement, Fabric trial eligibility, Entra group claims, and free-offer policy on this subscription remain **TODOs** in `DESIGN.md` §15. Until a short, approved portal session says otherwise, the open-source profile is the one that must always run.

---

## 4. Solution

See [`DESIGN.md`](DESIGN.md) for the architecture, rule IDs, profiles and demo script.

In one paragraph for a hiring manager: Northwind Advisory designs a versioned operating model over synthetic Customer, Product, Finance and HR data. Open Data Contract Standard contracts declare the critical elements. dbt builds domain marts. Great Expectations and dbt tests measure sourced quality rules. OpenMetadata holds the glossary (English with German aliases), lineage and tags. Our code holds ownership, the steward issue path, a short RoPA, retention flags, and a `fit_for_ai` export that a sibling AI gateway can consume. The same system can optionally read Azure SQL or Blob, map Entra groups to owners, and emit a note to Azure Monitor, then tear those resources down. A catalog vendor, and SAP MDG, are recommended where a client already has that pain or licence — they are not faked as hands-on product skills. `make demo` runs the story in under 15 minutes on the open-source profile; `make report` writes the PDF.

---

## 5. Results

Nothing has been measured yet. Every row stays **TO BE MEASURED** until a committed run with timestamp and git SHA exists. Do not fill this table from targets or memory.

| Result | Figure | Source (file, timestamp, git SHA) |
|---|---|---|
| Glossary coverage (definition + owner + steward on declared critical elements) | TO BE MEASURED | — |
| Quality — completeness, uniqueness, consistency, currentness on the synthetic set | TO BE MEASURED | — |
| Classification coverage on PII and confidential fields | TO BE MEASURED | — |
| Lineage coverage (one KPI dataset per domain to source) | TO BE MEASURED | — |
| Issue cycle in the demo (failed rule to recorded steward decision) | TO BE MEASURED | — |
| AI-label use on the fixture set | TO BE MEASURED | — |
| `make demo` duration (`oss`, after image pull) | TO BE MEASURED | — |
| Hybrid session: which adapters were live vs mocked, region, SKU, teardown, portal cost | TO BE MEASURED | — |

---

## 6. Roadmap and recommendation

Estimates below are design-planning figures only, not a booked delivery.

1. Agree the spec (`requirements.md`, `design.md`, `tasks.md`) on branch `spec` and stop for review.
2. Implement Phases 0–8 on the `oss` profile until `make demo` and `make report` run, and commit the first measured scorecard.
3. Only then, with an explicit go, run a short Germany West Central portal session for Phase 9 (Azure SQL and/or Blob, Entra if possible, optional Monitor, catalog adapter if still creatable). Write `docs/HYBRID.md`, capture results, delete the resources the same day.
4. Keep SAP MDG, Collibra and similar as documented buy options. Do not start a paid Fabric capacity. Do not start a Fabric trial without a separate, explicit go.
5. Publish labels to the existing AI Compliance Automation and gateway fixtures; do not merge those repos from here.

**Recommendation to the fictional client:** adopt the hybrid operating model. Buy a catalog if one is already licensed or if Fabric is already the group’s data platform; buy SAP MDG (or an equivalent) if master-data workflow in an SAP landscape is the actual pain; do not wait for those purchases before naming owners, writing contracts, measuring quality, completing a RoPA, and refusing unclassified data to assistants.

---
