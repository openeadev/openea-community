# OpenEA Community 1.5.2

OpenEA Community 1.5.2 establishes the clean, independently maintained Community baseline derived from OpenEA Community 1.5.1. This is a maintenance and product-identity release, not a feature release.

## What changed

- The Python distribution is now named `openea-community` so Community and Enterprise can have distinct package identities.
- The internal Python package remains `app`, preserving runtime commands, imports, Docker configuration, and upgrade compatibility.
- Added a distributable `.env.example` that matches the Docker Compose configuration.
- Added `.gitignore` and `.dockerignore` files suitable for a public Community repository and clean release archives.
- Removed generated caches and package metadata from the source release.
- Replaced hard-coded `1.5.1` labels in application templates with `settings.app_version`.
- Updated release metadata and regression expectations to version 1.5.2.
- Added Makefile and README support for installing, previewing, stopping, checking, and strictly building the MkDocs documentation site.
- Improved the relationship form so valid relationship choices are grouped alphabetically and target records are dynamically filtered to the selected governed target type.
- Target selectors now exclude archived records, retain Draft/Active/Inactive records, and sort records alphabetically by name.
- Relationship editing now permits changing the valid relationship type/target-type combination and target object while keeping the source object fixed.
- Fixed Impact Analysis HTTP filter parsing so relationship-type, result-object-type, and traversal-depth filters are applied together as documented.
- Impact Analysis now documents OR semantics within multi-select filters, AND semantics across filter groups, and preservation of explanatory intermediate path nodes.
- Added deterministic Attention reason explanations to the existing overdue Reviews workspace without broadening its scope.
- Expanded object Metrics pages with collapsible formulas, current inputs, components, missing/stale conditions, remediation guidance, and direct navigation links.
- Expanded the Community documentation with a technical metric-calculation reference and clearer metric interpretation guidance.
- Cleaned up the Acme Bank tutorial so system-behavior explanations use MkDocs information callouts instead of appearing as tutorial steps/headings.
- Added Platform Administrator-controlled periodic schedules for Analytics & Metrics and Findings Evaluation.
- Added controlled 15-minute through 24-hour interval choices, enable/disable controls, execution status, failure visibility, and asynchronous **Run now** actions.
- Extended the existing worker to check schedules approximately once per minute while retaining the existing approximately two-second job-queue polling behavior.
- Added overdue-schedule recovery: after downtime, a due process runs once and resumes from the current time rather than replaying every missed interval.
- Added migration `0016_phase15` for persisted scheduler settings and default schedules (metrics every 6 hours, findings every 1 hour).

## What did not change

- No Enterprise 1.6.x or 1.7.x capabilities were imported.
- Existing API authentication scopes remain unchanged. Relationship PATCH requests may optionally change the relationship type and target object, subject to the same metamodel validation as the browser UI.
- No repository object schema, authentication model, authorization roles/scopes, findings-rule vocabulary, import schema, portfolio formulas, or roadmap model changed. The only new schema is the scheduler settings table.
- Alembic head is now `0016_phase15`.

## Upgrade

OpenEA Community 1.5.1 installations can upgrade in place. Preserve the PostgreSQL data volume and `.env`, replace/rebuild the application, and allow the normal startup migration command to run. Migration `0016_phase15` creates the scheduler settings table without recreating architecture data. Confirm the database reaches `0016_phase15 (head)`.

See `docs/upgrading.md` for the detailed procedure.

## Front-end dependency note

The 1.5.2 baseline still uses the pinned jsDelivr references inherited from 1.5.1 for Tabler Core, HTMX, Lucide, and Cytoscape.js. Bundling those pinned third-party assets locally is intentionally tracked as a separate Community maintenance enhancement so the baseline does not silently substitute or modify third-party artifacts.

## Archived repository records

- Added archived-record discovery, visual relationship history, show/hide archived-related controls, direct archived-record viewing, and restore support.
