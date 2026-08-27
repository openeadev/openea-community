# Tutorial: Import Architecture Objects

Use the governed object CSV workflow when you have a set of records of the same object type to load or update.

## Example: import Technologies

Create a UTF-8 CSV such as:

```csv
name,description,lifecycle_stage,criticality,vendor,product,version,strategic_status
Example Database 1,Example database platform,Current,Medium,Example Vendor,Example Database,1.0,Tolerate
Example Runtime 2,Example runtime platform,Current,Medium,Example Vendor,Example Runtime,2.0,Strategic
```

## 1. Open Import

Sign in as an Architect or Architecture Administrator and choose **Management → Import**.

## 2. Choose Object CSV import

Select object type **Technology**, select the CSV file, and upload it.

## 3. Map columns

Map each CSV header to an allowed repository field or Technology property. A Name mapping is required.

Do not map a column if it does not represent a supported field.

## 4. Validate

Validation checks field types, enumerations, required values, and other metamodel constraints.

Rows are not committed at this stage.

## 5. Review preview

Each row is classified as:

- New
- Update
- Unchanged
- Error

OpenEA matches a supplied UUID first. Without a UUID, it matches exact case-insensitive Name within the selected object type.

Fix errors in the source CSV and repeat the workflow rather than forcing invalid rows through.

## 6. Commit

Commit only after the preview matches your intent. The import uses the same service-layer validation, auditing, and recalculation behavior as browser writes.

## Next step

Relationships are imported separately. See [CSV Import and Export](../user-guide/import-export.md) for the relationship workflow and endpoint-resolution rules.
