# Enterprise Data Governance & Quality Platform — Rules and Policies Catalog

**Status:** design catalog for the lab · no implementation, no measured results, no certification or compliance claim  
**Fictional client:** Tarsfeld Group GmbH (not a real firm) · synthetic Customer, Product, Finance and HR data only  
**Date verified:** 14 November 2026 (Europe/Berlin)  
**Companion figures:** [`diagrams/architecture.png`](diagrams/architecture.png), [`diagrams/architecture-explained.png`](diagrams/architecture-explained.png)  
**Companion design:** [`DESIGN-HIGHLEVEL.md`](DESIGN-HIGHLEVEL.md)

This catalog is a lab design aid. It is **not legal advice**, **not a GDPR or EU AI Act conformity assessment**, and **not a claim of certification** to ISO 8000, ISO/IEC 25012, ISO/IEC 38505-1 or ISO 9001. Full ISO texts are paid standards; clause numbers below are used only where the public ISO abstract (or, for EU law, the official Official Journal / EUR-Lex record) actually supports them. Where a public source does not give a clause number, the row cites the standard or official page only.

There is **no ISO 4001** in the data-quality or quality-management catalogue used here. Quality-management context is ISO 9001:2026 (a QMS standard, not a data standard). Data quality is taken from ISO 8000 and ISO/IEC 25012.

---

## 1. How to read a row

| Column | Meaning |
|---|---|
| **ID** | Stable lab identifier. `DQ-` = data-quality check; `POL-GDPR-` = GDPR-mapped policy/workflow; `GOV-` = operating-model rule; `AI-` = AI-label rule. |
| **Rule** | The plain-language requirement encoded in a data contract or workflow. |
| **Source** | The standard or legal article, plus what was actually verified. |
| **Domain** | Customer, Product, Finance, HR, or cross-domain. |
| **Check type** | Completeness, syntax, uniqueness, consistency, currentness, minimisation, retention, register, access, or workflow. |
| **Severity** | `critical` — block the quality gate and any `fit_for_ai` export; `high` — block the gate; `medium` — open a steward issue, allow a documented exception. |
| **Owner role** | RACI on the element: **Data Owner** is accountable; **Data Steward (Datenverantwortlicher)** is responsible for the check and the issue; **DPO** is consulted on personal-data policies. See §7 on why those titles are used. |
| **Action on fail** | What the platform does. A fail is never a silent skip. |

---

## 2. Source map (verified 14 November 2026, Europe/Berlin)

| Instrument | Official title / what was verified | Public source | How this lab uses it |
|---|---|---|---|
| **ISO 8000-8:2015** | *Data quality — Part 8: Information and data quality: Concepts and measuring.* Confirmed 2022. Abstract: fundamental concepts of information and data quality and how they apply to quality-management processes and systems; prerequisites for measuring information and data quality. The public abstract does **not** name syntactic, semantic or pragmatic quality, and publishes **no clause numbers**. | [iso.org/standard/60805.html](https://www.iso.org/standard/60805.html) | Context for *measuring* quality in the gate. Syntactic / semantic checks are **not** attributed to part 8. |
| **ISO 8000-61:2016** | *Data quality — Part 61: Data quality management: Process reference model.* Confirmed 2022. Abstract: specifies the processes required for data quality management, used as a reference to enhance data quality and assess process capability or organisational maturity. **No public clause numbers.** | [iso.org/standard/63086.html](https://www.iso.org/standard/63086.html) | The quality gate, steward issue and KPI scorecard are the lab’s process loop (measure → evaluate → act). Not a maturity-assessment claim. |
| **ISO 8000-110:2021** | *Data quality — Part 110: Master data: Exchange of characteristic data: Syntax, semantic encoding, and conformance to data specification.* Abstract (verified): computer-checkable requirements for messages that contain master data consisting of characteristic data, including conformance of messages to a **formal syntax**, **semantic encoding**, and **conformance to data specifications**. The same abstract places internal master-data management, accuracy, and non-message data **outside** the scope of part 110. **No public clause numbers.** | [iso.org/standard/78501.html](https://www.iso.org/standard/78501.html) | Principles only: a versioned data contract is the lab’s data specification; the quality gate checks computer-checkable syntax and conformance to that contract. This is **not** an implementation of ISO 8000-110 message exchange between organisations. |
| **ISO/IEC 25012:2008** | *Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model.* Confirmed 2025. Abstract: a general data quality model for structured data; **fifteen characteristics** considered from two points of view, **inherent** and **system-dependent**. The iso.org abstract does **not** name the fifteen characteristics and publishes **no clause numbers**. | [iso.org/standard/35736.html](https://www.iso.org/standard/35736.html) | The quality model the DQ rules are classified against. |
| **ISO/IEC 25012 characteristic names** | The public SQuaRE portal lists the inherent characteristics used in this catalog — **accuracy** (including syntactic and semantic accuracy), **completeness**, **consistency**, **credibility** and **currentness** — and gives definitions for accuracy, completeness and consistency. These names and definitions are **not** quoted from the paid ISO text. | [iso25000.com — ISO/IEC 25012](https://www.iso25000.com/index.php/en/iso-25000-standards/iso-25012) | Used to name the dimension of each DQ rule. Credibility is listed on that page but is not the primary dimension of a row below. |
| **Regulation (EU) 2016/679 (GDPR)** | Official Journal L 119, 4.5.2016. Wording of Art. 4(7), Art. 5(1)(c)(d)(e), Art. 25, Art. 30 and Art. 32 was read from the official English Official Journal PDF (Publications Office cellar `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`). The EUR-Lex HTML view returned only a stub on this date, so the PDF is the verification copy. | Official Journal PDF via the [Publications Office](https://op.europa.eu/en/publication-detail/-/publication/3e485e15-11bd-11e6-ba9a-01aa75ed71a1/language-en); CELEX [32016R0679](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) | Six concrete policies, each mapped to a check or workflow. |
| **Regulation (EU) 2024/1689 (EU AI Act)** | Official title of **Article 10** is **“Data and data governance”**, on the official EUR-Lex consolidated record (CELEX `02024R1689-20260727`, in force 27 July 2026). Official EUR-Lex search results for that consolidated text describe the dataset quality criteria as **relevant, sufficiently representative, and, to the best extent possible, free of errors and complete**. A full-text HTML fetch of EUR-Lex returned only a stub on this date, so **paragraph letters (for example 10(2) or 10(3)) are not cited as verified clause numbers in the rows below**. | [EUR-Lex consolidated text](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng) | Mapped to the `fit_for_ai` label only. The lab is not a high-risk AI system and this is not a conformity assessment. |
| **Council Directive 2006/112/EC, and Commission VAT page** | The Commission’s official “VAT identification numbers” page states that a VAT identification number **generally begins with the code of the country concerned followed by a block of digits or characters**, and that each EU country uses its own format. The same page points to **Article 214** of the VAT Directive for who must have a number. The official Annex 2 PDF verified on this date lists national *names* of the VAT number (Germany: *Umsatzsteuer-Identifikationsnummer*), **not** national digit patterns. A “DE + nine digits” pattern was **not** verified from these official pages and is **not** cited. | [taxation-customs.ec.europa.eu — VAT identification numbers](https://taxation-customs.ec.europa.eu/taxation/vat/vat-directive/vat-identification-numbers_en) | Syntactic check in `DQ-CUS-003`. |
| **DAMA-DMBOK2R** | DAMA International’s public pages state that DAMA-DMBOK organises data management into **11 knowledge areas**. The official infographics page names, among others, **Data Governance and Stewardship**, **Metadata Management**, **Reference and Master Data**, and **Data Quality Management**. DAMA-DMBOK is a body of knowledge, not a regulation. | [What is Data Management?](https://dama.org/about-dama/what-is-data-management/); [DMBOK2R infographics](https://dama.org/dmbok2r-infographics/) (cite: DAMA International, *DAMA-DMBOK2R*, 2nd ed. revised, Technics Publications, 2024) | Ownership / RACI, metadata / glossary, and MDM operating-model rows. |
| **ISO/IEC 38505-1:2026** | *Information technology — Governance of data — Part 1: Application of ISO/IEC 38500 to the governance of data.* Edition 2, published August 2026, supersedes the 2017 edition. Abstract: principles for governing bodies on the effective, efficient and acceptable use of data, by applying the governance principles and model of ISO/IEC 38500. **No public clause numbers.** | [iso.org/standard/87195.html](https://www.iso.org/standard/87195.html) | **Context only** — board-level data governance. Not implemented as a field check. |
| **ISO 9001:2026** | *Quality management systems — Requirements.* Edition 6, published September 2026, replaces ISO 9001:2015. A QMS standard for products and services, **not a data standard**. | [iso.org — ISO 9001:2026](https://www.iso.org/standard/9001) | **Context only** — quality culture and continual improvement around the operating model. |

---

## 3. Data quality rules (synthetic Tarsfeld data)

The quality gate (Great Expectations and dbt tests) is how ISO 8000-8’s *measuring* and ISO 8000-61’s *data quality management processes* show up in the architecture. Each row also names the ISO/IEC 25012 dimension it exercises, and, where the check is computer-checkable syntax or conformance to the data contract, ISO 8000-110’s published principles.

### DQ-CUS-001 — Customer email present and syntactically valid

| | |
|---|---|
| **Rule** | Every active customer contact record has an `email` value, and that value is syntactically valid against the data-contract pattern (a local part, `@`, and a domain). The pattern is the contract’s formal syntax, not a claim to implement a particular IETF RFC. |
| **Source** | ISO/IEC 25012:2008 — **completeness** and **accuracy** (syntactic accuracy is defined on the public ISO 25000 portal as closeness of a value to a domain considered syntactically correct). ISO 8000-110:2021 — computer-checkable **formal syntax** and **conformance to a data specification** (the contract). ISO 8000-8:2015 — measuring that quality concept. |
| **Domain** | Customer |
| **Check type** | Completeness + syntax |
| **Severity** | high |
| **Owner role** | Data Steward (Customer) responsible; Data Owner (Customer) accountable |
| **Action on fail** | Fail the quality gate; quarantine the record; open a steward issue; do not export the row; do not set `fit_for_ai`. |

### DQ-CUS-002 — Unique customer identifier

| | |
|---|---|
| **Rule** | `customer_id` is present and is unique in the customer master (no duplicate party keys across the two fictional country companies in the synthetic set). |
| **Source** | ISO/IEC 25012:2008 — **completeness** of the identifier, and **consistency** (the public portal: attributes free from contradiction and coherent with other data; inherent quality includes “relationships of data values”). ISO 8000-110:2021 — **conformance to a data specification** that requires a unique key. ISO 25012 does not publish a characteristic named “uniqueness”; this lab does not invent one. |
| **Domain** | Customer |
| **Check type** | Completeness + uniqueness (as consistency of the identifier) |
| **Severity** | critical |
| **Owner role** | Data Steward (Customer) responsible; Data Owner (Customer) accountable |
| **Action on fail** | Fail the quality gate; block the customer data product and any campaign export; open a steward issue to resolve or merge the keys. |

### DQ-CUS-003 — VAT identification number format, when present

| | |
|---|---|
| **Rule** | When a customer `vat_id` is present, it must begin with a country code followed by a block of digits or characters, and it must match the issuing country’s format as encoded in the data contract (the contract holds one syntactic pattern per country in the synthetic set). Empty is allowed only where the contract says the customer is not a VAT-registered taxable person. |
| **Source** | European Commission, *VAT identification numbers* (DG Taxation and Customs Union): a VAT identification number generally “begins with the code of the country concerned followed by a block of digits or characters”; each EU country uses its own format. ISO 8000-110:2021 — formal syntax and conformance to the data specification. ISO/IEC 25012:2008 — syntactic **accuracy**. A national pattern such as “DE plus nine digits” is **not** cited; it was not on the official pages verified on this date. |
| **Domain** | Customer (Finance is a consulted consumer of the same attribute) |
| **Check type** | Syntax (format), when present |
| **Severity** | high |
| **Owner role** | Data Steward (Customer) responsible; Data Owner (Customer) accountable; Finance Data Steward consulted |
| **Action on fail** | Fail the quality gate for that row; open a steward issue; do not use the VAT ID on a synthetic invoice or export until corrected. |

### DQ-PRD-001 — Product master: mandatory attributes present

| | |
|---|---|
| **Rule** | Every product master record carries the attributes declared mandatory in the product data contract: `product_id`, `name`, `status`, and `unit_of_measure`. |
| **Source** | ISO/IEC 25012:2008 — **completeness** (“subject data associated with an entity has values for all expected attributes”, public ISO 25000 portal). ISO 8000-110:2021 — **conformance to a data specification** for characteristic data of a master record (principle only; internal MDM is outside the published scope of part 110). DAMA-DMBOK2R — **Reference and Master Data** knowledge area, for ownership of those attributes. |
| **Domain** | Product |
| **Check type** | Completeness (mandatory attributes) |
| **Severity** | high |
| **Owner role** | Data Steward (Product) responsible; Data Owner (Product) accountable |
| **Action on fail** | Fail the quality gate; hold the product out of the product data product; open a steward issue. |

### DQ-FIN-001 — Cost centre referential integrity

| | |
|---|---|
| **Rule** | Every finance posting and every invoice line that carries a `cost_centre_id` must reference an identifier that exists, and is marked active, in the cost-centre reference list for that company code. |
| **Source** | ISO/IEC 25012:2008 — **consistency** (relationships of data values; attributes coherent with other data). ISO 8000-110:2021 — **semantic encoding** and **conformance to a data specification** (the code must decode against the agreed reference list). |
| **Domain** | Finance |
| **Check type** | Consistency (referential integrity) |
| **Severity** | critical |
| **Owner role** | Data Steward (Finance) responsible; Data Owner (Finance) accountable |
| **Action on fail** | Fail the quality gate; block the finance mart load for the row; open a steward issue; do not publish the related KPI until the key is resolved. |

### DQ-HR-001 — HR record currentness

| | |
|---|---|
| **Rule** | Every employee master record has a `status` and an `effective_from` date, and a `last_verified_on` date that is not older than the currentness window declared in the HR data contract (the window is a contract parameter, not a statutory retention period). A leaver must have an `effective_to` date. |
| **Source** | ISO/IEC 25012:2008 — **currentness** (named as an inherent characteristic on the public ISO 25000 portal; the iso.org abstract does not define it). Cross-reference: GDPR Art. 5(1)(d) — personal data shall be “accurate and, where necessary, kept up to date” (official OJ wording, verified). |
| **Domain** | HR (synthetic PII) |
| **Check type** | Currentness |
| **Severity** | high |
| **Owner role** | Data Steward (HR) responsible; Data Owner (HR) accountable; DPO consulted |
| **Action on fail** | Fail the quality gate; quarantine the employee record; open a steward issue; classify as `not_fit_for_ai`; no assistant or export path. |

---

## 4. GDPR policies (each mapped to a check or workflow)

Personal data in this lab exists only as synthetic Customer and HR records. The policies show *how* a specialist would operationalise the articles. They are not a claim that Tarsfeld Group, or any real firm, is compliant.

### POL-GDPR-01 — Data minimisation

| | |
|---|---|
| **Policy** | A data product or export of customer or HR data includes only the attributes that the approved purpose in the data contract declares as necessary. Extra attributes on the source extract are not copied forward by default. |
| **Source** | GDPR **Art. 5(1)(c)** — personal data shall be “adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed (‘data minimisation’).” Official OJ English, 4.5.2016. Supported by **Art. 25(2)** — by default, only personal data necessary for each specific purpose are processed (amount, extent, storage period and accessibility). |
| **Domain** | Customer, HR |
| **Check type** | Minimisation (contract + classification workflow) |
| **Severity** | critical |
| **Owner role** | Data Owner accountable; Data Steward responsible for the contract field list; DPO consulted |
| **Action on fail** | Block the export or data product; open a steward / DPO issue; no `fit_for_ai` label. |

### POL-GDPR-02 — Accuracy, and kept up to date

| | |
|---|---|
| **Policy** | Personal data in the customer and HR masters is subject to the quality gate (see DQ-CUS-001, DQ-CUS-002, DQ-HR-001). Inaccurate data is erased or rectified through the steward issue workflow without waiting for a later batch. |
| **Source** | GDPR **Art. 5(1)(d)** — personal data shall be “accurate and, where necessary, kept up to date; every reasonable step must be taken to ensure that personal data that are inaccurate, having regard to the purposes for which they are processed, are erased or rectified without delay (‘accuracy’).” Official OJ English, 4.5.2016. |
| **Domain** | Customer, HR |
| **Check type** | Workflow (quality gate + rectification issue) |
| **Severity** | high |
| **Owner role** | Data Steward responsible; Data Owner accountable; DPO consulted |
| **Action on fail** | Fail the quality gate; open a rectification issue; quarantine the row until it is corrected or formally excepted. |

### POL-GDPR-03 — Storage limitation / retention

| | |
|---|---|
| **Policy** | Each personal-data element carries a retention class and an intended erasure or archive date. A scheduled job flags rows past that date for erasure or for a documented archive purpose. The lab reports the flag; it does not perform production deletion. |
| **Source** | GDPR **Art. 5(1)(e)** — personal data shall be “kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed” (‘storage limitation’), with the official exceptions for archiving, research or statistics under Art. 89(1) and appropriate safeguards. Official OJ English, 4.5.2016. Linked register field: **Art. 30(1)(f)** — “where possible, the envisaged time limits for erasure of the different categories of data.” |
| **Domain** | Customer, HR |
| **Check type** | Retention (scheduled flag + RoPA time-limit field) |
| **Severity** | high |
| **Owner role** | Data Owner accountable; Data Steward responsible for the clock; DPO consulted |
| **Action on fail** | Flag the row as past retention; block new exports; open a steward / DPO issue for erasure or justified archive. |

### POL-GDPR-04 — Record of processing activities (RoPA)

| | |
|---|---|
| **Policy** | The lab maintains a written (electronic) record of processing for the Customer and HR synthetic processing activities, with the fields Art. 30(1) requires of a controller. |
| **Source** | GDPR **Art. 30(1)** — “Each controller and, where applicable, the controller's representative, shall maintain a record of processing activities under its responsibility.” The record shall contain: (a) names and contact details of the controller, any joint controller, representative and data protection officer; (b) purposes of the processing; (c) categories of data subjects and of personal data; (d) categories of recipients; (e) where applicable, transfers to a third country or international organisation; (f) where possible, envisaged time limits for erasure; (g) where possible, a general description of the technical and organisational security measures referred to in Art. 32(1). **Art. 30(3)** — the record shall be in writing, including in electronic form. Official OJ English, 4.5.2016. |
| **Domain** | Customer, HR (cross-domain register) |
| **Check type** | Register completeness (workflow) |
| **Severity** | high |
| **Owner role** | DPO accountable for the register’s existence; each Data Owner accountable for their activity’s entry; Data Steward responsible for keeping fields current |
| **Action on fail** | A processing activity without a RoPA entry cannot be approved for a new export or a `fit_for_ai` label; open a DPO issue. |

### POL-GDPR-05 — Data protection by design and by default

| | |
|---|---|
| **Policy** | Data contracts are designed so that, by default, only attributes necessary for the stated purpose are in the output schema, classification is applied at contract design time, and a new consumer does not receive an unfiltered source extract. |
| **Source** | GDPR **Art. 25(1)** — the controller shall, at the time of determining the means of processing and at the time of the processing itself, implement appropriate technical and organisational measures, “such as pseudonymisation, which are designed to implement data-protection principles, such as data minimisation, in an effective manner.” **Art. 25(2)** — by default, only personal data necessary for each specific purpose are processed (amount, extent, storage period and accessibility); by default, personal data are not made accessible without the individual’s intervention to an indefinite number of natural persons. Official OJ English, 4.5.2016. |
| **Domain** | Customer, HR |
| **Check type** | Workflow (contract design review) |
| **Severity** | high |
| **Owner role** | Data Owner accountable for the contract; Data Steward responsible; DPO consulted before a new personal-data product is published |
| **Action on fail** | Reject or revise the contract; do not publish the data product. |

### POL-GDPR-06 — Security of processing and access

| | |
|---|---|
| **Policy** | Access to classified personal data (`pii.contact`, `pii.hr`) is limited to named roles, logged, and granted only for a documented purpose. Persons with access process that data only on documented instructions. Classification and the access policy are the technical and organisational measures the lab actually demonstrates. |
| **Source** | GDPR **Art. 32(1)** — the controller and the processor shall implement appropriate technical and organisational measures to ensure a level of security appropriate to the risk, including inter alia as appropriate: (a) pseudonymisation and encryption; (b) ongoing confidentiality, integrity, availability and resilience of processing systems and services; (c) the ability to restore availability and access in a timely manner; (d) a process for regularly testing, assessing and evaluating the effectiveness of those measures. **Art. 32(4)** — the controller and processor shall take steps to ensure that any natural person acting under their authority who has access to personal data does not process them except on instructions from the controller, unless required by Union or Member State law. Official OJ English, 4.5.2016. |
| **Domain** | Customer, HR |
| **Check type** | Access control (policy check + classification) |
| **Severity** | critical |
| **Owner role** | Data Owner accountable; Data Steward and security/IT responsible for the control; DPO consulted |
| **Action on fail** | Deny access; deny the export; open a security / DPO issue; no `fit_for_ai` label. |

---

## 5. Operating-model rules (DAMA-DMBOK)

These are not statutory articles. They come from DAMA International’s Data Management Body of Knowledge (DAMA-DMBOK2R), whose public materials name eleven knowledge areas, including Data Governance and Stewardship, Metadata Management, and Reference and Master Data.

### GOV-RACI-01 — Named ownership for every critical element

| | |
|---|---|
| **Rule** | Every critical data element in the glossary has a named **Data Owner** (accountable) and a named **Data Steward (Datenverantwortlicher)** (responsible). The DPO is consulted where the element is personal data. |
| **Source** | DAMA-DMBOK2R knowledge area **Data Governance and Stewardship** (official infographics page; “What is Data Management?” describes Data Governance as establishing accountability, policies and decision rights). |
| **Domain** | Cross-domain |
| **Check type** | Workflow (RACI register completeness) |
| **Severity** | high |
| **Owner role** | Domain Data Owner accountable; Data Steward responsible for keeping the register current |
| **Action on fail** | The element cannot pass a “ready for use” review; `fit_for_ai` cannot be set; open a stewardship issue to nominate an owner. |

### GOV-META-01 — Glossary and technical metadata for critical elements

| | |
|---|---|
| **Rule** | Every critical element has a business definition (English, with a German alias where the Tarsfeld operating companies use one), a technical name, a classification tag, and a link to the data contract and quality rule that apply. |
| **Source** | DAMA-DMBOK2R knowledge area **Metadata Management** (official infographics page; “What is Data Management?” describes metadata as providing context and meaning so data is discoverable, usable and auditable). |
| **Domain** | Cross-domain |
| **Check type** | Workflow (catalog / glossary completeness) |
| **Severity** | medium |
| **Owner role** | Data Steward responsible; Data Owner accountable for the definition |
| **Action on fail** | Open a steward issue; the element is visible in the catalog as incomplete; it is not approved for a new consumer. |

### GOV-MDM-01 — Customer and product masters have a system of record

| | |
|---|---|
| **Rule** | `customer_id` and `product_id` (and the mandatory product attributes in DQ-PRD-001) have a documented system of record and a create-change-approve path. In this lab the path is documented on synthetic masters. For a real SAP landscape the design recommends buying SAP MDG (or an equivalent hub); the lab does not implement MDG. |
| **Source** | DAMA-DMBOK2R knowledge area **Reference and Master Data** (official infographics page). ISO 8000-110 is **not** cited as covering internal master-data management — its public abstract places that topic outside its scope. |
| **Domain** | Customer, Product |
| **Check type** | Workflow (MDM process) |
| **Severity** | high |
| **Owner role** | Data Owner accountable; Data Steward responsible |
| **Action on fail** | New or changed master values are not published to downstream marts until the documented path is followed. |

---

## 6. AI label — EU AI Act Article 10

### AI-FIT-01 — `fit_for_ai` only after governance and quality gates

| | |
|---|---|
| **Rule** | An asset or field may be labelled `fit_for_ai` only if all of the following are true: it has a named Data Owner and Data Steward (GOV-RACI-01); it is classified (including PII where applicable); the relevant quality-gate rules have passed; personal-data policies POL-GDPR-01, 02, 04 and 06 have been applied where the data are personal; and lineage to the source is recorded. Otherwise the label is `not_fit_for_ai`. This repo publishes the label; the Agent Access Governance Gateway and AI Compliance Automation consume it. |
| **Source** | EU AI Act, **Article 10 — “Data and data governance”** (official title on the EUR-Lex consolidated record, CELEX `02024R1689-20260727`). Official EUR-Lex search results for that text describe the quality criteria for training, validation and testing data sets of high-risk AI systems as **relevant, sufficiently representative, and, to the best extent possible, free of errors and complete**. Paragraph letters are not cited in this row because a full-text fetch of EUR-Lex was not available on the verification date. |
| **Domain** | Cross-domain (label export) |
| **Check type** | Workflow (label gate) |
| **Severity** | critical |
| **Owner role** | Data Owner accountable for the label; Data Steward responsible for the evidence pack; DPO consulted for personal data |
| **Action on fail** | Set `not_fit_for_ai`; do not include the asset in the AI label export as usable; the gateway path is `deny` or `ask`. |

**Scope note.** Article 10 applies to data used for high-risk AI systems. The Enterprise Data Governance & Quality Platform is **not** itself a high-risk AI system, and this catalog is **not** a conformity assessment. The mapping is a supply-side practice: data that might later be used by a high-risk system already carry classification, ownership, quality evidence and a `fit_for_ai` decision.

---

## 7. Role titles — why “Data Steward (Datenverantwortlicher)”

The 33-ad DACH and EU sample of 14 November 2026 uses the English titles **Data Steward** and **Data Owner** in the large majority of ownership and stewardship asks (24/33). That is the language hiring managers in this market actually use, including in German-language advertisements.

GDPR **Art. 4(7)** defines the **controller** as “the natural or legal person, public authority, agency or other body which, alone or jointly with others, determines the purposes and means of the processing of personal data.” In the official German text of the GDPR that legal role is **Verantwortlicher**. It is usually the organisation (here, the fictional Tarsfeld Group GmbH), not an individual operations role.

**Datenverantwortlicher** is sometimes used in German companies for the person accountable for a data domain. It is easy to confuse with *Verantwortlicher* in the Art. 4(7) sense. This lab therefore prints the bilingual operating-model label **Data Steward (Datenverantwortlicher)** on the architecture figure, and keeps the legal controller role off that figure on purpose. The **DPO** is a separate statutory function. The **Data Owner** is the RACI-accountable role for the domain or element.

---

## 8. Context standards (not implemented as field checks)

**ISO/IEC 38505-1:2026** applies the governance principles and model of ISO/IEC 38500 to the governance of data, for governing bodies (owners, directors, partners, executive managers or similar). It is the board-level frame around this operating model. It is not a source of field-level quality rules, and this lab does not invent clause numbers from it.

**ISO 9001:2026** specifies requirements for a quality management system for products and services. It is relevant only as context — quality culture, leadership, and continual improvement of the operating model. It is **not a data standard** and is not used as the source of a data-quality rule in §3.

---

## 9. What was not verified, and what was deliberately not cited

- **ISO 8000-8** public abstract does not mention syntactic, semantic or pragmatic quality. Those ideas, where used, are taken from the **ISO 8000-110:2021** abstract (formal syntax, semantic encoding, conformance to a data specification).
- **ISO/IEC 25012** iso.org abstract confirms fifteen inherent / system-dependent characteristics but does **not** name them. Names and the definitions of accuracy, completeness and consistency are taken from the public ISO 25000 portal, not from the paid ISO text. A paid-text definition of **currentness** and **credibility** was not verified; only the names appear on that portal’s introduction.
- **ISO 8000-110** clause numbers were not available from the public abstract. Internal MDM, accuracy, and non-message data are explicitly out of its published scope and are not attributed to it.
- **VAT national patterns** (for example DE + nine digits) were not on the official Commission page or Annex 2 as verified on this date, so they are not cited.
- **EU AI Act Article 10** paragraph letters were not re-verified from a full official text fetch on this date (EUR-Lex HTML returned a stub). The article title and the quality-criteria wording are taken from the official EUR-Lex record and official search results for the consolidated text of 27 July 2026.
- **Directive 2006/112/EC Art. 214** is mentioned on the Commission VAT page as the basis for who must have a VAT number; the article wording itself was not fetched, so the VAT *format* rule does not cite Art. 214 as its legal source.
- **No ISO 4001** was found or cited.
- No invented metrics, certification marks, or “compliant with” claims.
