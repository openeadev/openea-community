# Acme Bank: Build an Enterprise Architecture Repository from Scratch

This hands-on tutorial is for users who installed **OpenEA Community 1.5.2** and intentionally did **not** load the Northstar Financial demo repository.

You will start with an empty architecture repository and progressively build the fictitious **Acme Bank** model using the OpenEA browser interface. The tutorial is designed to be both a learning path and a repeatable reference for the core OpenEA Community workflows.

!!! important "Version scope"
    Every field, role, relationship, governance transition, finding rule, and workflow in this tutorial is based on the OpenEA Community **1.5.2** implementation. If you are using a different version, check that version's documentation before assuming the screens or validation rules are identical.

## What you will build

By the end of the sequence, your repository will contain a coherent banking architecture with all twelve standard OpenEA object types represented.

```text
Acme Bank
│
├── Business
│   ├── Consumer Banking                       [Business Product]
│   ├── Customer Management                    [Business Capability]
│   ├── Deposit Account Management             [Business Capability]
│   ├── Payments                               [Business Capability]
│   ├── Regulatory Reporting                   [Business Capability]
│   ├── Open Customer Account                  [Business Process]
│   ├── Process Customer Payment               [Business Process]
│   ├── Acme Bank                              [Organization]
│   ├── Retail Banking                         [Organization]
│   ├── Payments Technology                    [Organization]
│   ├── Enterprise Architecture                [Organization]
│   ├── Head of Retail Banking                 [Role]
│   ├── Payments Application Owner             [Role]
│   └── Enterprise Architect                   [Role]
│
├── Applications
│   ├── Digital Banking                        [Application]
│   ├── Core Banking                           [Application]
│   ├── Payments Hub                           [Application]
│   ├── Legacy Wire Transfer                   [Application]
│   ├── Digital Account Service                [Application Service]
│   └── Payment Processing Service             [Application Service]
│
├── Information
│   ├── Customer                               [Data Object]
│   ├── Account                                [Data Object]
│   ├── Payment                                [Data Object]
│   └── Regulatory Report                      [Data Object]
│
├── Technology
│   ├── Java 21                                [Technology]
│   ├── PostgreSQL 17                          [Technology]
│   ├── Kubernetes                             [Technology]
│   └── Java 8                                 [Technology]
│
├── Change
│   ├── Digital Banking Modernization          [Initiative / Project]
│   └── Legacy Wire Retirement                 [Initiative / Project]
│
└── Governance
    ├── Prefer Strategic Technologies          [Architecture Principle]
    └── Standardize Digital Channels on Java 21 [Architecture Decision]
```

The base tutorial model contains **32 architecture objects** before the optional CSV-import additions. You will then connect those objects with governed relationships and deliberately model several architecture problems so you can see OpenEA findings and analytics respond to repository changes.

## The learning sequence

Work through these pages in order. Later pages assume the objects created by earlier pages already exist.

1. [Prepare a clean OpenEA environment](00-prepare-environment.md)
2. [Create Acme Bank organizations and roles](01-organizations-and-roles.md)
3. [Model the business architecture](02-business-architecture.md)
4. [Model applications and application services](03-application-architecture.md)
5. [Model data and technology](04-data-and-technology.md)
6. [Connect the architecture with relationships](05-relationships.md)
7. [Model initiatives and architecture change](06-initiatives.md)
8. [Add governance, reviews, principles, and decisions](07-governance.md)
9. [Use findings and analytics](08-findings-and-analytics.md)
10. [Run impact analysis](09-impact-analysis.md)
11. [Use portfolios and roadmaps](10-portfolios-and-roadmaps.md)
12. [Import additional data with CSV](11-csv-imports.md)
13. [Edit, remediate, and archive records](12-lifecycle-and-cleanup.md)

## How this tutorial avoids duplicating the reference documentation

The tutorial tells you **what to do with Acme Bank and why**. It does not attempt to redefine every OpenEA concept on every page.

Use these existing pages whenever you need the full product rules:

- [Objects and Metadata](../../concepts/objects.md) — conceptual model for architecture objects
- [Manage Architecture Objects](../../user-guide/objects.md) — general create/edit/archive workflow
- [Standard Metamodel](../../reference/metamodel.md) — object types and supported properties
- [Relationships](../../concepts/relationships.md) — relationship concepts
- [Manage Relationships](../../user-guide/relationships.md) — general relationship workflow
- [Relationship Vocabulary](../../reference/relationships.md) — valid source/relationship/target combinations
- [Users and Permissions](../../administration/users-permissions.md) — authorization model
- [Findings](../../user-guide/findings.md) and [Built-in Finding Rules](../../reference/finding-rules.md)
- [Analytics and Repository Health](../../user-guide/analytics.md)
- [CSV Import and Export](../../user-guide/import-export.md)

When a tutorial step references one of those subjects, follow the tutorial values and use the linked reference page for the complete rules.

## Tutorial conventions

Unless a step says otherwise, use these repository metadata values when creating Acme Bank records:

| Field | Tutorial default |
| --- | --- |
| Record status | `Active` |
| Governance status | Leave as the system-managed initial value (`Draft`) |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |
| Tags | `Acme Bank` |

Some object types do not expose a lifecycle field. When a lifecycle field is present, the tutorial gives the exact value to choose.

!!! note "Governance status is workflow-controlled"
    The create/edit form displays Governance status, but OpenEA 1.5.2 changes governance through the **Lifecycle** tab rather than by editing that field directly. Architecture Principles and Architecture Decisions also have their own controlled status transitions.

## Deliberately imperfect architecture data

Real repositories are not perfect. The tutorial intentionally creates several conditions that should produce findings, including:

- **Legacy Wire Transfer** without an owner organization or owner role
- **Legacy Wire Transfer** without a capability mapping
- **Legacy Wire Transfer** with missing Technical Fit
- **Legacy Wire Transfer** using **Java 8**, which is modeled as end-of-support and marked `Retire`
- **Regulatory Reporting** with no supporting application
- **Regulatory Report** with no system-of-record relationship
- An intentionally overdue architecture review

Do not “fix” those items early. Chapter 8 uses them to demonstrate deterministic findings, and Chapter 13 uses selected items to demonstrate remediation.

## If your repository is not empty

This sequence is written for an empty repository. If you already created records, you can still follow it, but duplicate names may cause import matching or relationship-selection differences later.

For the cleanest learning experience, use a fresh OpenEA Community installation with the standard metamodel seeded but without `seed-demo`.
