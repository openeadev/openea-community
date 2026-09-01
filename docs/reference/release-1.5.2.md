# OpenEA Community 1.5.2

OpenEA Community 1.5.2 establishes the independently maintained Community baseline derived from 1.5.1. It is primarily a maintenance, product-identity, and deployment-support release rather than a new schema release.

## Baseline characteristics

- Python distribution name: `openea-community`
- Internal Python package: `app`
- Python compatibility: 3.10+
- PostgreSQL: 16+ baseline
- Alembic head: `0015_phase15`
- License: AGPLv3

## Database compatibility

There is no new schema migration from 1.5.1 to 1.5.2. Existing repository objects, relationships, users, tokens, findings, audit history, and configuration remain compatible.

## Community deployment model

The standard Docker Compose runtime remains:

```text
PostgreSQL
   ▲
   ├── OpenEA web
   └── OpenEA worker
```

The optional public Render demo uses a free web service and free PostgreSQL database. Its startup script runs the web process and existing background worker in the same Render container because the free tier does not include a separate worker service.

## Front-end dependencies

The 1.5.2 baseline still loads pinned Tabler Core, HTMX, Lucide, and Cytoscape.js assets through jsDelivr. Local vendoring of those third-party assets is not part of the baseline.

## Quality and explainability updates

Later 1.5.2 maintenance updates also include:

- corrected Impact Analysis parsing for relationship and result-object multi-select filters
- explicit OR-within-filter / AND-across-filter semantics with explanatory intermediate paths preserved
- an Attention reason column in the existing overdue Reviews workspace
- expanded View Metrics cards with deterministic formulas, inputs, components, missing/stale information, response guidance, and navigation links
- a detailed [Metric Calculation Reference](analytics-metrics.md)
- clearer Acme Bank tutorial information callouts for system-controlled behavior

These changes do not add a database migration; Alembic remains at `0015_phase15`.
