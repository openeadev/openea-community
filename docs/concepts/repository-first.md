# Repository-first Architecture

OpenEA Community treats structured repository data as the authoritative Enterprise Architecture model.

## One model, many views

The same objects and relationships drive multiple experiences:

```text
Architecture Repository
        │
        ├── Explore and search
        ├── Object detail pages
        ├── Relationship views
        ├── Impact Analysis
        ├── Analytics
        ├── Repository Health
        ├── Findings
        ├── Portfolios
        ├── Capability Map
        └── Roadmaps
```

A diagram, portfolio table, risk score, or roadmap is therefore a view of repository information rather than a separately maintained source of truth.

## Why this matters

A manually maintained diagram can become stale as soon as the underlying systems change. In OpenEA, the durable information is the object and relationship model. Visualizations are regenerated from it.

For example, if `Customer Portal` stops using `PostgreSQL 17` and begins using another Technology, update the relationship in the repository. Impact Analysis and related views then use the updated model.

## Repository data is governed

Repository-first does not mean "store anything." OpenEA 1.5.2 validates:

- Standard object types
- Type-specific fields
- Enumerated values
- Object references
- Relationship types
- Valid relationship source/target combinations
- Relationship-specific properties

This balances flexibility with consistent architectural meaning.

## History is part of the model

OpenEA generally archives architecture objects and relationships rather than deleting them. Significant changes also generate audit events. This supports a repository that can explain how the architecture changed, not only what the current state looks like.
