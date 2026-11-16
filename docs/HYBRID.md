# Hybrid profile runbook (Phase 9)

The `hybrid` profile adds optional, feature-flagged, environment-only (`DG_*`)
Azure adapters on top of the oss core. **Everything defaults to a mock.** With
no `DG_*` credentials set, every adapter resolves to its mock and `make demo`
still runs on the oss path. CI only ever runs oss.

This runbook is for a short, operator-approved **create → test → delete** portal
session. Nothing here spends credit until you choose to create a resource, and
every resource is torn down in the same session.

## Hard rules (enforced in code and in this runbook)

- **Region: Germany West Central only.** A configuration naming any other region
  is rejected (`DG_AZURE_REGION` must be Germany West Central).
- **Portal-only creation.** Azure CLI device-code login is blocked by
  Conditional Access in this environment; create and delete resources in the
  portal.
- **Smallest / free tiers only.** Create → test → delete in one session. Never
  select "continue with charges".
- **HR stays local.** The HR domain is never bound to an Azure source. The code
  raises if anything tries; keep it that way.
- **Catalog defaults to mock.** No live Purview / Fabric by default. Do **not**
  start a Fabric trial and do **not** buy a paid Fabric F SKU.
- **No secrets in the repo.** All credentials are `DG_*` environment variables,
  supplied at run time. Do not commit them. Do not put a subscription identifier
  in the README or any committed artefact.

## Resources to create for the live test (smallest possible)

Create these three, in **Germany West Central**, then delete them (see Teardown):

1. **Azure SQL Database — Finance source.** General Purpose **serverless**, with
   **auto-pause enabled** (pause after the minimum idle, e.g. 1 hour) so it
   stops billing when idle; use the free offer if available, otherwise the
   smallest **Basic** tier. One small database; load only the non-HR Finance
   extract. Never choose "continue with charges" if a free limit is reached.
2. **One Azure Storage account — Product source.** StorageV2, **Standard**,
   **LRS**, Hot tier, smallest configuration, with a single short-lived
   container for the Product CSV/Parquet extract.
3. **One Azure Monitor / Log Analytics workspace (optional).** Smallest SKU,
   shortest retention. Optional evidence sink; skip it if the SKU is not clearly
   free or tiny.

Entra ID group-to-owner mapping is adapter-only and needs no new billable
resource; it is used only if an app registration and group claims are available
on the subscription (unverified — mock otherwise). No catalog resource is
created (catalog stays mocked).

## Environment variables (`DG_*`, supplied at run time, never committed)

```
DG_PROFILE=hybrid
DG_AZURE_REGION=germanywestcentral

# Azure SQL (Finance) — live read uses the optional pymssql driver
DG_AZURE_SQL_SERVER=...
DG_AZURE_SQL_DATABASE=...
DG_AZURE_SQL_USER=...
DG_AZURE_SQL_PASSWORD=...
DG_AZURE_SQL_TABLE=finance_postings   # optional, default finance_postings

# Azure Blob (Product) — live read uses stdlib urllib + a read-only SAS
DG_AZURE_STORAGE_ACCOUNT=...
DG_AZURE_STORAGE_CONTAINER=...
DG_AZURE_STORAGE_SAS=...               # read-only container SAS (preferred)
DG_AZURE_STORAGE_BLOB=products.csv     # optional, default products.csv

# Entra (optional; mock if unavailable)
DG_ENTRA_TENANT_ID=...
DG_ENTRA_CLIENT_ID=...

# Azure Monitor (optional)
DG_AZURE_MONITOR_WORKSPACE_ID=...

# Catalog stays mocked by default; do not set to purview/fabric without a go.
DG_CATALOG_BACKEND=mock
```

Any variable left unset makes its adapter fall back to the mock.

### Driver for the Azure SQL live read

The Azure Blob live read needs **no** driver (standard-library `urllib` over
HTTPS with the read-only SAS). The Azure SQL live read needs the optional
`pymssql` driver:

```
pip install pymssql          # or: pip install .[hybrid]
```

If the `DG_AZURE_SQL_*` credentials are set but `pymssql` is not installed, the
adapter raises a clear error and tells you to install it — it never silently
falls back to the mock. The connection uses TLS (TDS 7.4, port 1433).

## Cost notes

- Azure SQL **serverless with auto-pause** bills compute only while active; an
  idle database auto-pauses. Prefer the free offer; otherwise the smallest Basic
  tier is a few currency units per month and is deleted the same day.
- One smallest StorageV2 Hot LRS account with a tiny container and same-day
  deletion is a negligible, near-zero charge.
- A smallest Log Analytics workspace with shortest retention is optional; skip
  it unless it is clearly free or tiny.
- Capture the portal cost (or a zero-charge screenshot) into the run folder
  **before** deleting, if a cost figure will be reported. Never report an
  invented figure.

## Smoke test

1. **Seed the Finance table.** Generate the seed SQL from the synthetic finance
   extract and paste it into the Azure portal **Query editor**:

   ```
   python3 scripts/hybrid_seed.py      # writes scripts/hybrid_seed_sql.sql
   ```

   The script uses only the synthetic finance extract (no HR, no real data). Run
   the generated `CREATE TABLE` + `INSERT` statements against the database.
2. **Upload the Product blob.** Upload `data/raw/product/products.csv` to the
   container as `products.csv` (or set `DG_AZURE_STORAGE_BLOB` to its name) and
   mint a **read-only container SAS** for `DG_AZURE_STORAGE_SAS`.
3. Set the `DG_*` variables for the resources you created (and
   `pip install pymssql` for the SQL read).
4. Run the smoke:

   ```
   python -m dgqp.cli hybrid-smoke
   ```

   It reads the non-HR domains from whichever adapters are live (Finance from
   SQL, Product from Blob), runs the quality gate over the rows it got, prints
   which adapters are live vs mock with per-domain row counts and findings, and
   writes `eval/results/hybrid-<UTC>.json` (live and mock separated; region
   recorded; no secret, server/account name or subscription id written). It
   asserts HR was not touched by any Azure adapter.
5. Optionally run `make demo`; confirm the hybrid posture line and that the
   catalog sync reports **mock**.

## Teardown checklist (same session)

- [ ] Capture the portal cost / zero-charge screenshot into the run folder (if
      reporting cost).
- [ ] Delete the Azure SQL Database (and its logical server if created for this).
- [ ] Delete the Storage account (and the container within it).
- [ ] Delete the Log Analytics workspace, if created.
- [ ] Remove any Entra app registration created for the test, if applicable.
- [ ] Delete the resource group if it was created only for this session.
- [ ] Unset the `DG_*` environment variables.
- [ ] Confirm in the portal that no resource from this session remains.

## Results

**TO BE MEASURED (live session pending).**

No live hybrid numbers exist. After an approved create-test-delete session,
record here — with a UTC timestamp and git SHA — which adapters ran **live** vs
**mocked**, the region, the SKU, the measured portal cost (or zero), and that
teardown completed. Keep live and mock results separate; never blend them, and
never invent a figure.
