# What is OpenEA Community?

OpenEA Community is an open-source **Enterprise Architecture Management** platform. It stores architecture information as structured objects and governed relationships, then derives analysis and decision-support views from that repository.

## More than an inventory

An application inventory can tell you that an organization owns a system named `Customer Portal`. An Enterprise Architecture repository should help explain why that system matters.

For example:

```text
Customer Management
        ▲
        │ supports
        │
Customer Portal
        │
        ├── uses ──► Amazon EKS
        │
        └── uses ──► PostgreSQL 17
```

That connected information lets an architect move from questions such as "What systems do we have?" to questions such as:

- What business capability relies on this application?
- What technologies create technical exposure for it?
- Which initiatives are changing it?
- What else could be affected by retiring it?

## The standard repository

OpenEA Community 1.5.2 provides twelve standard architecture object types:

| Domain | Object types |
| --- | --- |
| Business | Business Product, Business Capability, Business Process, Organization, Role |
| Application | Application, Application Service |
| Information | Data Object |
| Technology | Technology |
| Change | Initiative / Project |
| Governance | Architecture Principle, Architecture Decision |

Each object combines universal metadata—such as status, criticality, ownership, source, confidence, review dates, aliases, and tags—with type-specific fields defined by the metamodel.

## Governed relationships

OpenEA does not allow arbitrary relationship labels between arbitrary object types. Relationship types have governed source and target rules.

Examples include:

- Application **supports** Business Capability
- Application **uses** Technology
- Application **depends on** Application
- Application **system of record for** Data Object
- Initiative **changes** Application
- Architecture Decision **selects** Technology
- Architecture Decision **supersedes** Architecture Decision

The relationship is stored once. OpenEA can display an inverse label when you view it from the target object. For example, `Application supports Business Capability` can appear from the capability side as `supported by Application` without creating a second relationship row.

## Repository-first architecture

OpenEA treats the repository as authoritative. Derived views include:

```text
Repository
   ├── Search and filtering
   ├── Object visualizations
   ├── Impact Analysis
   ├── Analytics and risk
   ├── Repository Health
   ├── Findings
   ├── Portfolios
   ├── Capability maps
   └── Roadmaps
```

This avoids making a manually maintained diagram or dashboard a competing source of truth.

## Explainable analysis

OpenEA's persisted metrics and findings are deterministic. A user can inspect the inputs and component explanations behind calculated metrics rather than receiving an unexplained score.

Examples include:

- Application Risk
- Technology Risk
- Capability Risk
- Data Quality
- Impact Severity
- Repository Health dimensions
- Finding evidence

## Governance and history

OpenEA separates architecture lifecycle from governance state. An Application can be lifecycle `Active` while its governance status is `Approved`, `Needs Review`, or another governed state.

OpenEA also supports:

- Review cycles and overdue-review tracking
- Comments on architecture objects
- Architecture Decision Records
- Decision supersession
- Immutable audit events
- Soft archival of architecture objects and relationships

## What OpenEA is not

OpenEA is not primarily:

- A CMDB
- An infrastructure inventory
- A ticketing system
- A project-management application
- A freeform diagramming tool
- A cloud-management platform

Those systems may provide useful evidence or source data. OpenEA's role is to preserve architectural meaning and the relationships that support enterprise-level analysis.

## Next step

Continue with the [OpenEA Community live demo](live-demo.md) to see these concepts in the Northstar Financial repository.
