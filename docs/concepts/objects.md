# Objects and Metadata

An **architecture object** is a governed repository record representing something meaningful to Enterprise Architecture.

## Standard object types

OpenEA Community 1.5.2 seeds twelve system object types:

- Business Product
- Business Capability
- Business Process
- Organization
- Role
- Application
- Application Service
- Data Object
- Technology
- Initiative / Project
- Architecture Principle
- Architecture Decision

## Universal metadata

All architecture objects share a common set of repository fields, including:

- Name
- Description
- Record Status
- Governance Status
- Lifecycle Stage, when applicable
- Criticality
- Owner Organization
- Owner Role
- Source
- Confidence
- Valid From / Valid Until
- Last Reviewed / Next Review
- Review Frequency
- Aliases
- Tags
- Created / Updated timestamps
- Archived timestamp

## Type-specific metadata

Each object type adds fields defined by its metamodel schema. Examples:

**Application** adds business fit, technical fit, strategic fit, hosting model, vendor/product/version, retirement dates, RTO/RPO, data classification, and internet-facing status.

**Technology** adds category, vendor/product/version, lifecycle, strategic status, support-end dates, replacement technology, and approved-for-new-use status.

**Business Capability** adds parent capability, maturity, target maturity, and strategic importance.

The browser form is schema-driven. OpenEA rejects unknown properties, invalid types, invalid governed values, malformed dates, bad object references, and missing required properties.

## Architecture Role vs application role

The `Role` object type is an Enterprise Architecture repository object representing a business or architecture responsibility. It is separate from OpenEA authorization roles such as Architect or Viewer.

This distinction is important:

```text
Repository Role object
    "Digital Application Owner"

is not the same as

OpenEA application role
    "Architect"
```
