# OpenEA Community 1.5.2

OpenEA Community 1.5.2 establishes the independently maintained Community baseline derived from 1.5.1. It is a maintenance, product-identity, deployment-support, and operational-control release. Later 1.5.2 maintenance updates add a small scheduler schema while preserving the 1.5.2 product version.

## Baseline characteristics

- Python distribution name: `openea-community`
- Internal Python package: `app`
- Python compatibility: 3.10+
- PostgreSQL: 16+ baseline
- Alembic head: `0017_phase15`
- License: AGPLv3

## Database compatibility

OpenEA Community 1.5.2 remains an in-place upgrade from 1.5.1. Maintenance migration `0016_phase15` creates `scheduled_job_settings` for Platform Administrator-controlled background-processing schedules, and `0017_phase15` creates the generic `application_settings` table used by optional login reCAPTCHA. Existing repository objects, relationships, users, tokens, findings, metrics, audit history, and configuration are preserved.

## Community deployment model

The standard Docker Compose runtime remains:

```text
PostgreSQL
   ▲
   ├── OpenEA web
   └── OpenEA worker
```

The optional public Render demo uses a free web service and free PostgreSQL database. Its startup script runs the web process and existing background worker in the same Render container because the free tier does not include a separate worker service.

## Front-end dependencies and offline runtime

Community 1.5.2 maintenance now vendors the browser dependencies into the OpenEA Docker image at build time. Tabler Core, HTMX, Lucide, Cytoscape.js, Swagger UI, and ReDoc are served locally from `/static/vendor`, so the installed application does not need a public CDN during normal runtime. Swagger UI's external validator is disabled and ReDoc does not load Google Fonts.

The first connected image build may still need Internet access to pull Docker base images, download Python packages, and retrieve the pinned browser files. A separate [Offline and Air-Gapped Installation](../getting-started/offline-installation.md) procedure documents how to build/export the application and PostgreSQL images on a connected preparation host and load them on an isolated target.

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

Scheduled background processing adds migration `0016_phase15`; optional login reCAPTCHA adds `0017_phase15` for generic application settings. Existing architecture and governance data are preserved.
## Optional login reCAPTCHA

A later 1.5.2 maintenance update adds optional Google reCAPTCHA v2 protection to the interactive login form. The visible checkbox is disabled by default. `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` are deployment environment variables, while the Platform Administrator's enabled/disabled selection is persisted in `application_settings`.

When enabled, reCAPTCHA is verified server-side before password authentication and verification outages fail closed. When disabled, no Google reCAPTCHA browser resource or server verification request is used, preserving normal offline operation.

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
