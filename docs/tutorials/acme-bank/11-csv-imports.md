# 12. Import Additional Architecture Data with CSV

So far, you have built Acme Bank manually. That is the best way to learn the repository model, but real architecture teams often need to load larger data sets.

OpenEA Community 1.5.2 intentionally separates **object CSV import** from **relationship CSV import**. This chapter uses both workflows.

For complete limits, matching behavior, and resolution rules, see [CSV Import and Export](../../user-guide/import-export.md).

## Goal

You will:

1. Import two additional Applications.
2. Preview the import before committing it.
3. Import relationships from those Applications to existing Acme objects.
4. Observe how imported architecture changes findings.
5. Learn an important 1.5.2 limitation: object CSV import does not map structured owner organization/owner role fields.

## 1. Create the Application CSV file

On your workstation, create a file named:

```text
acme-applications.csv
```

Paste this content exactly:

```csv
name,description,record_status,lifecycle_stage,criticality,application_type,business_owner,technical_owner,business_fit,technical_fit,strategic_fit,hosting_model,delivery_model,data_classification,internet_facing,source,confidence,review_frequency,tags
Regulatory Reporting Platform,Application used to prepare and retain regulatory reporting information.,Active,Active,High,Custom,Regulatory Reporting,Regulatory Technology,Good,Good,Good,Private Cloud,Internal,Confidential,false,Imported,High,Annual,"Acme Bank, CSV Tutorial"
Fraud Monitoring,Application used to monitor payment activity for potential fraud.,Active,Active,High,Custom,Risk Management,Fraud Technology,Good,Good,Good,Private Cloud,Internal,Restricted,false,Imported,High,Annual,"Acme Bank, CSV Tutorial"
```

The file contains only Applications because the object import workflow imports **one selected object type at a time**.

## 2. Upload the object CSV

Sign in as your Architect user.

1. Select **Management → Import**.
2. In **Object CSV import**, choose **Application** as the Object type.
3. Choose `acme-applications.csv`.
4. Select **Upload object CSV**.

OpenEA reads the headers and opens **Map CSV columns**.

## 3. Verify the object mappings

OpenEA suggests mappings when a column name matches a common field or a valid property for the selected object type.

Verify these mappings:

| CSV column | OpenEA field |
| --- | --- |
| `name` | Name |
| `description` | Description |
| `record_status` | Record Status |
| `lifecycle_stage` | Lifecycle Stage |
| `criticality` | Criticality |
| `application_type` | Application Type (property) |
| `business_owner` | Business Owner (property) |
| `technical_owner` | Technical Owner (property) |
| `business_fit` | Business Fit (property) |
| `technical_fit` | Technical Fit (property) |
| `strategic_fit` | Strategic Fit (property) |
| `hosting_model` | Hosting Model (property) |
| `delivery_model` | Delivery Model (property) |
| `data_classification` | Data Classification (property) |
| `internet_facing` | Internet Facing (property) |
| `source` | Source |
| `confidence` | Confidence |
| `review_frequency` | Review Frequency |
| `tags` | Tags |

The exact labels in the dropdown are title-cased, and schema properties are identified as properties.

!!! important "Name is required"
    At least one CSV column must map to **Name**. OpenEA rejects a mapping that omits it.

Select **Validate and preview**.

## 4. Read the object preview

For a repository that followed the tutorial exactly, the preview should show:

```text
New:       2
Update:    0
Unchanged: 0
Error:     0
```

Review both rows and confirm they are valid.

Nothing has been written to the architecture repository yet. Preview is deliberately separate from commit.

If the preview shows an error, do not commit. Select **Change mapping**, correct the mapping or CSV data, and validate again.

## 5. Commit the object import

When the batch status is `Validated`, select **Commit import**.

OpenEA creates the two Applications through the normal ObjectService, records audit history with source `CSV Import`, and queues background recalculation work.

Return to **Explore** and filter to Applications. You should now have:

- Core Banking
- Digital Banking
- Fraud Monitoring
- Legacy Wire Transfer
- Payments Hub
- Regulatory Reporting Platform

## 6. Understand the structured-owner limitation in 1.5.2

Open the imported **Regulatory Reporting Platform**.

You entered free-text Application properties such as Business Owner and Technical Owner, but the common object-import field list in OpenEA Community 1.5.2 does **not** include:

```text
owner_organization_id
owner_role_id
```

Therefore, the imported Application's structured **Owner organization** and **Owner role** remain unset.

This is not a CSV error. It is the supported 1.5.2 import schema.

You will set those fields manually in the next chapter. Until then, `APP-OWNER-001` can identify the imported applications as lacking structured ownership.

## 7. Create the relationship CSV file

Now create:

```text
acme-relationships.csv
```

with this content:

```csv
source_type,source_name,relationship_type,target_type,target_name,criticality,confidence,source
Application,Regulatory Reporting Platform,supports,Business Capability,Regulatory Reporting,High,High,Imported
Application,Regulatory Reporting Platform,system_of_record_for,Data Object,Regulatory Report,High,High,Imported
Application,Regulatory Reporting Platform,uses,Technology,PostgreSQL 17,Medium,High,Imported
Application,Fraud Monitoring,supports,Business Capability,Payments,High,High,Imported
Application,Fraud Monitoring,reads,Data Object,Payment,High,High,Imported
Application,Fraud Monitoring,uses,Technology,Java 21,Medium,High,Imported
```

This file uses exact object names, which is the simplest relationship endpoint strategy for a manually curated import.

## 8. Upload the relationship CSV

1. Return to **Management → Import**.
2. In **Relationship CSV import**, choose `acme-relationships.csv`.
3. Select **Upload relationship CSV**.

The relationship mapping page requires these three fields at minimum:

- Source Type
- Relationship Type
- Target Type

You must also provide a usable identifier for each endpoint. In this file you use Source Name and Target Name.

## 9. Verify the relationship mappings

Confirm:

| CSV column | OpenEA relationship field |
| --- | --- |
| `source_type` | Source Type |
| `source_name` | Source Name |
| `relationship_type` | Relationship Type |
| `target_type` | Target Type |
| `target_name` | Target Name |
| `criticality` | Criticality |
| `confidence` | Confidence |
| `source` | Source |

Select **Validate and preview**.

## 10. Review endpoint resolution and validation

OpenEA Community 1.5.2 resolves relationship endpoints in this order:

1. UUID
2. External ID when the governed object properties expose one
3. Exact case-insensitive name
4. Exact case-insensitive alias

Your file uses exact names, so the source and target objects should resolve without ambiguity.

The importer also validates the relationship vocabulary. For example:

```text
Application → supports → Business Capability
```

is valid, while an arbitrary unsupported source/type/target combination would fail preview.

For the canonical tutorial repository, expect:

```text
New:       6
Update:    0
Unchanged: 0
Error:     0
```

## 11. Commit the relationship import

Select **Commit relationship import**.

OpenEA commits the relationships through the normal RelationshipService, including:

- Server-side metamodel validation
- Audit events
- CSV Import source/correlation information
- Recalculation jobs

## 12. Verify the imported model in Explore

Open **Regulatory Reporting Platform → Relationships**.

You should see:

```text
Regulatory Reporting Platform
├── supports → Regulatory Reporting
├── system of record for → Regulatory Report
└── uses → PostgreSQL 17
```

Open **Fraud Monitoring → Relationships**:

```text
Fraud Monitoring
├── supports → Payments
├── reads → Payment
└── uses → Java 21
```

## 13. Recalculate and evaluate findings again

Run:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

Then return to **Findings**.

Several conditions should change because the imported relationships changed the architecture model:

### Regulatory Reporting capability

Before import:

```text
0 supporting applications → CAP-APP-001
```

After import:

```text
Regulatory Reporting Platform supports Regulatory Reporting
```

The no-support condition should no longer be active. Because the capability now has exactly one supporting application, the single-application-dependency rule (`CAP-APP-002`) can become the relevant condition instead.

### Regulatory Report Data Object

Before import:

```text
no system of record → DATA-SOR-001
```

After import:

```text
Regulatory Reporting Platform system of record for Regulatory Report
```

The no-system-of-record condition should resolve on reevaluation.

### Payments capability

Before import, Payments had exactly one supporting Application (Payments Hub). Fraud Monitoring now also supports Payments, so the single-application-dependency condition should no longer apply to Payments.

### Imported application ownership

Both new Applications still lack structured Owner organization / Owner role values because those fields are not supported by the 1.5.2 object CSV mapping. Expect ownership findings until you correct them manually.

## 14. Optional: demonstrate alias resolution

Digital Banking has the alias:

```text
Online Banking
```

If you want to test alias endpoint resolution, make a temporary relationship CSV row that references `Online Banking` as `source_name` with source type Application. Use a relationship that is not already present, or expect an existing relationship to preview as `Unchanged` if the same active relationship already exists.

Remove or avoid committing experimental rows if you want to keep the canonical Acme model predictable.

## 15. Optional: demonstrate object update matching

Object imports match an existing object by:

1. Supplied UUID, then
2. Exact case-insensitive Name within the selected object type.

If you upload an Application row named exactly `Fraud Monitoring` again with a mapped description change, preview should classify the row as `Update` rather than creating a duplicate.

This is useful for controlled bulk maintenance, but remember that only mapped fields participate in the imported change.

## Checkpoint

You have now exercised both governed import paths:

```text
Object CSV
Upload → Map → Validate/Preview → Commit

Relationship CSV
Upload → Map → Resolve/Validate/Preview → Commit
```

The important safety property is that CSV input does not bypass the application model. Imported changes still pass through validation and auditing.

Continue to [Edit, Remediate, Govern, and Archive](12-lifecycle-and-cleanup.md).
