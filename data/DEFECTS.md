# Seeded defects in the synthetic extracts

Synthetic data only, two country companies: `DE01` (German HQ) and `AT01`. Each
`DQ-*` rule in [`docs/RULES-AND-POLICIES.md`](../docs/RULES-AND-POLICIES.md) has
at least one failing row so the demo can show the gate failing closed and a
steward cleanse. HR is local-only.

| Rule | File | Failing row(s) | Defect |
|---|---|---|---|
| `DQ-CUS-001` | `raw/customer/customers.csv` | `C-DE-1003`, `C-AT-2002` | email empty; email not syntactically valid |
| `DQ-CUS-002` | `raw/customer/customers.csv` | `C-DE-1001` (DE01 + AT01) | `customer_id` reused across the two companies (not unique) |
| `DQ-CUS-003` | `raw/customer/customers.csv` | `C-DE-1004` | `vat_id` present but violates the DE contract pattern (`DE12AB`) |
| `DQ-PRD-001` | `raw/product/products.csv` | `P-102`, `P-201` | missing `name`/`unit_of_measure`; missing `status` |
| `DQ-FIN-001` | `raw/finance/finance_postings.csv` | `F-4`, `F-5` | cost centre not in reference; cost centre inactive |
| `DQ-FIN-001` (consistency) | `raw/finance/finance_control_totals.csv` | `DE01` | reported total 350.00 ≠ sum of DE01 postings 375.00 (does not reconcile). AT01 reconciles (200.00 = 200.00) on purpose, so only DE01 is the seeded reconciliation defect. |
| `DQ-HR-001` | `raw/hr/employees.csv` | `E-3`, `E-4`, `E-5` | stale `last_verified_on`; leaver with no `effective_to`; missing `status` |

Allowed (not a defect): `C-AT-2003` has an empty `vat_id`, which the Customer
contract permits for a customer that is not a VAT-registered taxable person
(`DQ-CUS-003`).

The HR currentness window is a contract parameter, not a statutory retention
period. The VAT per-country pattern is a contract parameter for the synthetic
set and is **not** an official VAT format (see `docs/RULES-AND-POLICIES.md`
`DQ-CUS-003`).
