# Findings Engine

OpenEA Community findings are deterministic analytical records derived from repository facts. Findings are not architecture objects and do not become authoritative architecture truth.

## Finding lifecycle

Supported statuses are Open, Acknowledged, Accepted, Remediation Planned, Resolved, and Dismissed. Dismissal requires a reason. Status, assignment, resolution, dismissal, and rule-administration changes are audited.

When a rule condition clears, active findings are automatically resolved. A previously resolved finding reopens if the condition returns. Dismissed findings remain dismissed while the condition continues to exist.

## Declarative rule types

OpenEA Community 1.5.0 supports only these governed rule types:

- `date_threshold`
- `missing_field`
- `missing_relationship`
- `related_object_status`
- `relationship_count`
- `risk_threshold`
- `review_overdue`
- `duplicate_name`

No user-provided Python or arbitrary executable expression is accepted.

## Custom rules

Architecture Administrators manage rules at `/admin/finding-rules`.

Custom rules can be created, edited, enabled/disabled, and deleted from the UI. OpenEA validates rule configuration against active object types, relationship types, known universal/object-specific fields, supported metrics, directions, thresholds, and counts before saving it.

Custom rules receive stable display IDs such as `CUSTOM-0001`. Deleting a custom rule performs soft archival rather than destructive deletion. The rule is disabled and hidden from the active administration list while historical findings and audit events remain available.

## Built-in rules

OpenEA seeds sixteen built-in rules covering technology lifecycle, application ownership/mapping, capability dependencies, service duplication, systems of record, reviews, application risk, initiative collision, retired technology exposure, and missing technical fit/review dates.

Built-in rules cannot be deleted. Their name, rule type, description, and applicability remain protected. Architecture Administrators may adjust supported operational parameters such as severity, date windows, relationship count bounds, risk thresholds, and configured related-status values. Startup seeding does not overwrite those administrator-tuned parameters.

## Evaluation

Repository and relationship writes can queue metric and finding recalculation. Rule create/edit/toggle/delete actions also queue finding evaluation.

Administrative commands remain available:

```bash
python -m app.cli evaluate-findings
python -m app.cli evaluate-findings-now
```


## Findings workspace default view

Beginning with 1.5.1, the Findings workspace hides `Resolved` findings by default so the operational list focuses on current conditions. Resolved findings are retained historically and can be displayed with **All statuses** or **Resolved** in the status filter. Deleting a custom rule remains a soft archival operation; historical findings are not hard-deleted.
