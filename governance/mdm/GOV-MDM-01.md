# GOV-MDM-01 — System of record and create-change-approve path

`customer_id` and `product_id` (and the mandatory product attributes in
`DQ-PRD-001`) have a documented system of record and a create-change-approve
path. In this lab the path is documented on synthetic masters. For a real SAP
landscape the design recommends **buying SAP MDG** (or an equivalent hub); the
lab does **not** implement MDG and this is not SAP experience.

Source: DAMA-DMBOK2R *Reference and Master Data* knowledge area
(see `docs/RULES-AND-POLICIES.md` GOV-MDM-01).

## Systems of record (synthetic lab)

| Master | System of record (lab) | Key | Buy option in a real landscape |
|---|---|---|---|
| Customer | `data/raw/customer/customers.csv` | `customer_id` | SAP MDG / an MDM hub |
| Product | `data/raw/product/products.csv` | `product_id` | SAP MDG / an MDM hub |

## Create-change-approve path

1. **Create.** A new master value is proposed by the domain. It must satisfy the
   ODCS contract (mandatory attributes, key uniqueness).
2. **Change.** A change is raised against the system of record only. Downstream
   marts read from the system of record, never a side copy.
3. **Approve.** The Data Steward (Datenverantwortlicher) checks the quality
   rules for the element; the Data Owner approves. Until the documented path is
   followed, a new or changed master value is **not** published to downstream
   marts (the on-fail action for GOV-MDM-01).

## Why not clone SAP MDG

Reference- and master-data workflow (create-change-approve with governance,
duplicate handling, hierarchies) is exactly what SAP MDG and comparable hubs
sell. Cloning that is out of scope (v1). The honest recommendation is to buy it
where an SAP landscape has that pain, and to keep ownership, the quality rule
pack and the issue workflow — the differentiated work — as our own.
