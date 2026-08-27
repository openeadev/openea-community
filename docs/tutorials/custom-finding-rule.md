# Tutorial: Create a Custom Finding Rule

OpenEA Community allows Architecture Administrators to create governed **declarative** finding rules. Custom rules do not execute arbitrary Python code.

## Example goal

Create a rule that identifies Applications missing a chosen field or property.

## 1. Open Finding Rules

Sign in as an **Architecture Administrator** and choose:

**Management → Finding Rules → New**

## 2. Choose a supported rule type

OpenEA 1.5.2 supports these declarative rule types:

- missing_field
- date_threshold
- missing_relationship
- relationship_count
- related_object_status
- risk_threshold
- review_overdue
- duplicate_name

For this tutorial choose **missing_field**.

## 3. Define the rule

Use a clear name and description. Select Application as the object type, choose a supported universal or Application-specific field, select severity, and enable the rule.

OpenEA validates internal field names against the metamodel. A rule cannot reference arbitrary undefined properties.

## 4. Save and evaluate

Saving a rule queues finding evaluation. You can also trigger evaluation administratively:

```bash
python -m app.cli evaluate-findings
```

For immediate troubleshooting:

```bash
python -m app.cli evaluate-findings-now
```

## 5. Inspect evidence

Open any resulting Finding. Confirm that its evidence explains why the repository object matched the rule.

## 6. Understand custom-rule lifecycle

Custom rules receive IDs such as:

```text
CUSTOM-0001
```

Deleting a custom rule is a soft archival operation. OpenEA disables and archives the rule while preserving historical findings and audit events.

Built-in rules cannot be deleted.
