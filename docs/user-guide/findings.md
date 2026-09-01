# Findings

Findings turn deterministic repository conditions into actionable architecture work.

## Findings are evidence-based

A finding has a rule, severity, related architecture object, status, detection/evaluation timestamps, assignment information, and stored evidence.

OpenEA Community 1.5.2 does not require arbitrary Python code for custom finding rules. Custom rules are declarative and validated against supported rule types, fields, metrics, object types, and relationship vocabulary.

## Finding statuses

The Findings workspace focuses on current conditions. Resolved findings are hidden by default in 1.5.2 but remain available through status filtering.

Users with Contributor, Architect, or Architecture Administrator permissions can update finding status and assignment information. A dismissal requires a dismissal reason.

## Built-in rules

OpenEA seeds sixteen built-in rules. Examples include:

- Technology past or approaching end of support
- Application using retiring technology
- Application without owner
- Application without capability mapping
- Capability without application support
- Capability with a single supporting application
- Potential duplicate Application Service names
- Data Object without a system of record
- Conflicting systems of record
- Overdue architecture review
- High-risk Mission Critical application
- Initiative change collision
- Active application linked to retired technology
- Missing technical fit
- Missing review date

See [Built-in Finding Rules](../reference/finding-rules.md) for the complete list.

## Finding Rules administration

Architecture Administrators can open **Management → Finding Rules**.

Built-in rules cannot be deleted. Supported operational parameters can be tuned without changing the rule's fundamental meaning.

Custom rules receive IDs such as `CUSTOM-0001`. Deleting a custom rule performs soft archival: the rule is disabled and hidden from the active administration list while historical findings and audit events remain.

## Evaluation

Repository and relationship changes can queue finding evaluation. Rule create/edit/toggle/archive operations also queue evaluation.

OpenEA also reevaluates findings on the **Findings Evaluation** schedule maintained by a Platform Administrator under **Management → Background Processing**. The default interval is one hour. This keeps date-driven findings current even when the repository has been idle.

Administrators can also queue or synchronously run evaluation from the CLI:

```bash
python -m app.cli evaluate-findings
python -m app.cli evaluate-findings-now
```

The CLI commands themselves are not scheduled commands. See [Worker and Background Calculations](../administration/worker-jobs.md) for the event-driven and periodic processing model.
