# OpenEA Community 1.5.2

OpenEA Community 1.5.2 establishes the independently maintained Community baseline derived from 1.5.1. It is a maintenance, product-identity, deployment-support, and operational-control release. Later 1.5.2 maintenance updates add a small scheduler schema while preserving the 1.5.2 product version.

## Baseline characteristics

- Python distribution name: `openea-community`
- Internal Python package: `app`
- Python compatibility: 3.10+
- PostgreSQL: 16+ baseline
- Alembic head: `0016_phase15`
- License: AGPLv3

## Database compatibility

OpenEA Community 1.5.2 remains an in-place upgrade from 1.5.1. A later 1.5.2 maintenance update adds migration `0016_phase15`, which creates `scheduled_job_settings` for Platform Administrator-controlled background-processing schedules. Existing repository objects, relationships, users, tokens, findings, metrics, audit history, and configuration are preserved.

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
- Platform Administrator-controlled periodic schedules for Analytics & Metrics and Findings Evaluation
- controlled 15-minute through 24-hour intervals, enable/disable controls, execution status, and asynchronous **Run now** actions
- overdue schedule recovery that runs once after downtime instead of replaying every missed interval

Scheduled background processing adds migration `0016_phase15`; existing architecture and governance data are preserved.
## Archived repository records

Community 1.5.2 maintenance updates preserve soft-archived objects as searchable historical records. Explore hides archived records by default but supports **Archived** and **All records** scopes. Existing relationships remain stored. The browser Relationships tab hides historical entries by default; **Show archived** reveals relationships to archived objects and archived relationship records using the normal light/dark theme background plus an **Archived** badge. Authorized users can restore an archived object without recreating its preserved relationships.

## Additional 1.5.2 quality fixes

- Relationship target selection is filtered to the governed target type, excludes archived objects, and is sorted alphabetically.
- Relationship editing can change a valid relationship type/target pair while preserving the source object.
- Object alias updates preserve unchanged aliases and deduplicate duplicate aliases case-insensitively.
- Role **Owner organization** and **Role organization** are explicitly independent concepts and may be the same or different.
- Object-reference properties display referenced object names rather than raw UUID values in the repository detail view.
- Unexpected browser errors use a branded error page with a Request ID; unexpected API errors return a safe message and Request ID while detailed exceptions remain in server logs.
- Archived Explore and Relationships rows use normal theme-controlled backgrounds in both light and dark mode; archive state is communicated through badges, status, dates, filtering, and historical controls.

## Documentation and demo deployment

- Added the MkDocs/Material documentation site published at `docs.openea.dev`.
- Added the Acme Bank hands-on tutorial for learning from an empty repository while retaining Northstar Financial as the populated evaluation model.
- Added README/Makefile workflows for local documentation preview and strict builds.
- Documented the optional Render public-demo pattern, including commit-aware reset/reseed behavior, `/health/ready`, Psycopg 3 URL normalization, and running the worker in the small demo web container.
- Community navigation branding identifies the Community edition, while theme-sensitive graph and archived-state rendering now remain readable in both light and dark modes.
