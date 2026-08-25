# CSV Import and Export

OpenEA Community provides separate governed CSV workflows for architecture objects and architecture relationships at `/imports`. Both are available to Architects and Architecture Administrators.

## Object import

The object workflow remains Upload → Choose object type → Map columns → Validate → Preview → Commit. Uploaded CSV content and preview state are retained in PostgreSQL as an `import_batches` record.

CSV files must be UTF-8, no larger than 5 MB, and no more than 5,000 data rows. A Name mapping is required. Common repository fields and schema-defined object properties are valid mapping targets. Boolean values accept `true/false`, `yes/no`, `1/0`, and `y/n`. Multi-select values use `|` as the CSV cell delimiter.

Object matching is deterministic: supplied UUID first, then exact case-insensitive Name within the selected object type. Preview classifies every row as New, Update, Unchanged, or Error.

## Relationship import

Relationship import is a separate workflow so relationship resolution and metamodel validation remain explicit. Each row should identify a source object, governed relationship type, and target object.

Endpoint resolution order is:

1. UUID, when supplied.
2. External ID, when the object's governed properties expose one.
3. Exact case-insensitive object name.
4. Exact case-insensitive alias.

Object type values may be the OpenEA Community metamodel key (`application`, `technology`) or exact display name (`Application`, `Technology`). Ambiguous matches remain errors in preview; OpenEA Community does not choose among multiple candidates.

The importer supports description, criticality, confidence, validity dates, source, and relationship-specific governed properties. Relationship types and source/target combinations are validated against the metamodel. Existing source/type/target triples are classified as Update or Unchanged rather than creating duplicate inverse rows.

A typical relationship CSV is:

```csv
source_type,source_name,relationship_type,target_type,target_name,criticality,confidence
Application,Customer Portal,uses,Technology,PostgreSQL 17,High,Confirmed
Application,Customer Portal,supports,Business Capability,Customer Management,High,High
```

See `examples/relationship-import.csv` for a ready-to-edit sample.

## Audit and commit behavior

Invalid imports cannot be committed. Relationship commits use the normal `RelationshipService`, including server-side validation, audit events, and recalculation jobs. All changes in one relationship batch use audit source `CSV Import` and correlation ID `relationship-csv-import:<batch UUID>`.

## Export

Filtered object CSV export remains available at `/exports/objects.csv` and honors supported query/object-type/status/criticality filters.
