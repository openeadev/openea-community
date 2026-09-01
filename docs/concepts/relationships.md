# Relationships

Relationships provide the context that turns a collection of records into an Enterprise Architecture model.

## Governed vocabulary

OpenEA Community 1.5.2 seeds 25 relationship types. Each relationship type specifies valid source and target object types.

For example:

```text
Application ── supports ──► Business Capability
Application ── uses ──────► Technology
Initiative  ── changes ───► Application
```

OpenEA rejects combinations that are not defined by the metamodel.

## One stored relationship, two readable directions

Relationships are stored once. The relationship type also contains an inverse display label.

For example:

```text
Stored:
Customer Portal ── supports ──► Customer Management

Viewed from the capability:
Customer Management ◄── supported by ── Customer Portal
```

OpenEA does not create a duplicate inverse relationship row.

## Relationship metadata

Relationships can include:

- Description
- Criticality
- Confidence
- Valid From
- Valid Until
- Source
- Governed relationship-specific properties

The `integrates with` relationship supports additional metadata including integration type, protocol, direction, criticality, description, and data exchanged.

## Relationships drive analysis

Repository relationships are used by:

- Object relationship tabs
- Impact Analysis
- Capability support counts
- Technology dependent-application counts
- Risk calculations
- Findings
- Portfolios
- Roadmaps and change context

## Relationship history and archived objects

Archiving an architecture object does not delete its relationships. OpenEA preserves them so historical architecture remains explainable and so restoration does not require relationship recreation.

The browser Relationships tab shows current relationships by default. **Show archived** reveals both relationships to archived objects and relationship records that were independently archived. Historical entries use the normal theme background plus an **Archived** badge and are read-only in that view. Archived objects are not offered as targets for new relationships.
