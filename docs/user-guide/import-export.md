# CSV Import and Export

OpenEA provides separate governed workflows for object and relationship CSV imports under **Management → Import**.

Only Architects and Architecture Administrators can import. Any authenticated user can export repository objects.

## Limits

Both import workflows enforce:

- CSV format
- UTF-8 content
- Maximum file size of 5 MB
- Maximum 5,000 data rows
- Validation and preview before commit

## Object import workflow

The object workflow is:

```text
Upload → Choose object type → Map → Validate → Preview → Commit
```

A Name mapping is required. Columns can map to common repository fields or valid properties for the selected object type.

Object matching is deterministic:

1. Supplied UUID
2. Exact case-insensitive Name within the selected object type

Preview classifies rows as:

- New
- Update
- Unchanged
- Error

Boolean cells accept common forms such as `true/false`, `yes/no`, `1/0`, and `y/n`. Multi-select values use `|` inside the CSV cell.

## Relationship import workflow

Relationship import is intentionally separate from object import.

Endpoint resolution order is:

1. UUID
2. External ID when the object's governed properties expose one
3. Exact case-insensitive object name
4. Exact case-insensitive alias

Ambiguous matches remain errors. OpenEA does not silently choose among several candidates.

A typical file looks like:

```csv
source_type,source_name,relationship_type,target_type,target_name,criticality,confidence
Application,Customer Portal,uses,Technology,PostgreSQL 17,High,Confirmed
Application,Customer Portal,supports,Business Capability,Customer Management,High,High
```

Object type values can use either metamodel keys such as `application` or exact display names such as `Application`.

The importer validates relationship vocabulary, source/target applicability, and relationship properties before commit.

## Audit behavior

Committed relationship rows go through the normal RelationshipService, including server-side validation, audit events, and recalculation jobs. Relationship CSV batches use audit source `CSV Import` and a batch correlation ID.

## Export

Filtered object export is available from `/exports/objects.csv`. Export honors supported query, object type, record status, and criticality filters across the full result set, not only the current UI page. If Explore is filtered to **Archived** or **All records**, export uses the same archival scope.
