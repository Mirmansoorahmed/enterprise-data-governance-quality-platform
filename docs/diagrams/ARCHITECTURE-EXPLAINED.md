# Enterprise Data Governance & Quality Platform — how to read the architecture

The published figure is [`architecture.png`](architecture.png) and [`architecture.svg`](architecture.svg). A second figure, [`architecture-explained.png`](architecture-explained.png) (and [`.svg`](architecture-explained.svg)), is the same diagram with numbered markers and a legend panel underneath: one or two lines on what each component does and which rule source drives it.

The figures are a left-to-right flow in four lanes. Everything in the lab is synthetic. Nothing on the diagram is a measured result.

Concrete, source-cited rules — rule ID, plain-language rule, standard or article, domain, check type, severity, owner role and action on fail — are in [`../RULES-AND-POLICIES.md`](../RULES-AND-POLICIES.md). That catalog is the traceable source for the quality gate, the GDPR policies, the ownership model and the `fit_for_ai` label. It is a lab design aid, not legal advice and not a certification or conformity claim.

The public name, locked 14 November 2026, is **Enterprise Data Governance & Quality Platform** (repo `enterprise-data-governance-quality-platform`). The working folder stays `data-governance-automation`.

Frequencies below are from the 33-ad DACH and EU sample in [`../../research/data-governance-market-general-2026-11.md`](../../research/data-governance-market-general-2026-11.md).

---

## The four lanes

**1. Data sources.** Four domains sit in one box: Customer, Product, Finance and HR. The extracts are synthetic only, so the demo can show a multi-domain operating model without using real people or a real employer. Master data of this kind appears in 16/33 ads; the general market is not only sales or SAP.

**2. Data contracts and the quality gate.** A contract declares the critical data elements and the rule that must hold before a record moves on (the lab’s data specification; ISO 8000-110 is cited for the *principle* of computer-checkable syntax and conformance to a specification, not as an implemented message-exchange standard). The quality gate (Great Expectations and dbt tests) then checks completeness, uniqueness, consistency and currentness, classified against ISO/IEC 25012 and measured in the spirit of ISO 8000-8 and ISO 8000-61. The box is tagged **ISO 8000 / ISO/IEC 25012**. Example rules — customer email present and valid, unique customer ID, VAT ID format, product mandatory attributes, cost-centre referential integrity, HR currentness — are in the catalog. Data quality is the most common ask in the sample (30/33). Data contracts are rare in the ads themselves (1/33); they are in the lab because they make those quality rules testable, not because HR is searching for the phrase.

**3. Governance core.** This is the operating model a specialist actually runs. The catalog and glossary (20/33) hold definitions, in English with German aliases (DAMA-DMBOK Metadata Management). Lineage (13/33) traces a KPI back to its source. Classification, with a short RoPA and access/retention policy, covers the privacy cluster (13/33 combined). Ownership / RACI names a Domain Data Owner and a Data Steward (Datenverantwortlicher) for each element (24/33; DAMA-DMBOK Data Governance and Stewardship). Policies and standards are written down, not only implied (18/33). Classification and Policies carry the source tag **GDPR Art. 5/30/32**. The mapped articles — Art. 5(1)(c) minimisation, 5(1)(d) accuracy, 5(1)(e) storage limitation, Art. 25 privacy by design, Art. 30 RoPA, Art. 32 security and access — are in the catalog, each tied to a check or workflow.

**4. Consumers.** The KPI scorecard reports the quality dimensions — as TARGETS until a committed run exists. Domain data products are the dbt marts served under the contract. The AI label export sends classification, owner and `fit_for_ai` to the already-built AI Compliance Automation service and the Agent Access Governance Gateway (AI overlap is 7/33 ads). The box is tagged **EU AI Act Art. 10** (Data and data governance). This repo does not make the allow / deny decision, and the mapping is not a high-risk AI conformity assessment.

Under the lanes, three small strips sit out of the main flow on purpose. **People in the loop** are the Data Owner, the Data Steward (Datenverantwortlicher) and the DPO. **Optional buy** is one dashed box for Microsoft Purview, Collibra and SAP MDG — recommended or mapped, not built (Purview 6/33, Collibra 10/33, SAP MDG as a product 8/33). **A request can end in** pass, a steward fix, or deny / ask.

---

## Why the figure says “Data Steward (Datenverantwortlicher)”

DACH job ads in the 33-ad sample overwhelmingly use the English titles **Data Steward** and **Data Owner**, including in German-language vacancies (ownership and stewardship in 24/33). That is the language this market hires for.

GDPR Art. 4(7) defines the **controller**. In the official German text of the GDPR that legal role is **Verantwortlicher** — usually the organisation, not an individual operations role. **Datenverantwortlicher** is sometimes used in German companies for the person accountable for a data domain, but it is easy to confuse with *Verantwortlicher* in the Art. 4(7) sense. The figure therefore prints the bilingual operating-model label **Data Steward (Datenverantwortlicher)**, and keeps the legal controller off the people strip on purpose. The longer note is in [`../RULES-AND-POLICIES.md`](../RULES-AND-POLICIES.md) §7.

---

## One request, end to end

A commercial user asks: “Export these customers for a local campaign.”

1. The customer extract is already under a data contract: the campaign list has a named owner, a definition, and quality rules from the catalog (for example, unique `customer_id`, a present and syntactically valid email, a VAT ID that matches the contract format when present). Classification limits the export to attributes the purpose needs (GDPR Art. 5(1)(c) and Art. 25).
2. The quality gate runs. If a row fails, the happy path stops and a steward issue is opened. The Data Steward (Datenverantwortlicher) records a decision, a cleanse or a rule change is versioned, and the gate is re-run. That is the business–IT interface those ads hire for, and it is also how Art. 5(1)(d) (accuracy, rectified without delay) shows up as a workflow.
3. If the gate passes, the catalog can show the definition, the owner, the lineage to the source, and the classification. The RoPA entry for the activity must exist (Art. 30) before a new export is approved. The approved set can feed the KPI scorecard or a dbt data product.
4. If someone then asks an assistant to use that list, the label pack is what the gateway sees. A non-PII, already-approved KPI aggregate can be `allow`. A customer extract tagged `pii.contact` or `not_fit_for_ai` is `deny` or `ask`. `fit_for_ai` is set only when ownership, classification, the quality gate and the relevant GDPR policies are already in place (EU AI Act Art. 10).

---

## Why each component is there

| Component | Why it is on the diagram | Rule source (see the catalog) | Frequency (n = 33) |
|---|---|---|---|
| Four domain sources | The project has to fit more than one industry and more than sales data | Synthetic data only; the four domains carry the DQ and GDPR rules | Master data / MDM 16/33 |
| Data contracts | Turns standards into a testable agreement | ISO 8000-110 (principle: conformance to a data specification) | Named in 1/33; used here as a method, not a keyword bet |
| Quality gate | The job almost every ad describes | ISO 8000-8 / 8000-61 / 8000-110 and ISO/IEC 25012; rules `DQ-CUS-001` to `DQ-HR-001` | 30/33 |
| Catalog & glossary | Definitions and a place to find them | DAMA-DMBOK Metadata Management (`GOV-META-01`) | 20/33 (glossary named in 6/33) |
| Lineage | A number must be traceable | Evidence path for the other rules | 13/33 |
| Classification + policies / RoPA | Privacy, access and retention, written down | GDPR Art. 5, 25, 30 and 32 (`POL-GDPR-01` to `06`) | Privacy / classification 13/33; policies 18/33 |
| Ownership / RACI | Someone is accountable | DAMA-DMBOK Data Governance and Stewardship (`GOV-RACI-01`) | 24/33 |
| KPI scorecard | Quality work has to be visible | ISO 8000-61 (process); ISO/IEC 25012 (dimensions) | Part of the 30/33 quality ask |
| Data products (dbt) | The approved output the business can actually use | Served under the contract, after the gate | dbt itself is rare in ads; the *function* is the trusted dataset |
| AI label export | Data used by agents must already be classified and owned | EU AI Act Art. 10 (`AI-FIT-01`) | 7/33 |
| People in the loop | Owners, stewards and a DPO stay in the design | See the role note above | Stewardship 24/33; DPO / privacy as above |
| Optional buy (Purview, Collibra, SAP MDG) | Honest buy-versus-build, not a fake product skill | Not a rule source | Purview 6/33, Collibra 10/33, SAP MDG 8/33 |

OpenMetadata and Great Expectations were not named in the 33 ads. They are the default open-source path so the demo still runs without a cloud account. DAMA-DMBOK / DCAM (9/33) is mapped in the case-study pack and in the rules catalog, not drawn as a separate box. ISO/IEC 38505-1:2026 and ISO 9001:2026 are context only in that catalog; ISO 9001 is not a data standard. There is no ISO 4001 in this design.
