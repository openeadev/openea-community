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

## What did not change

- No Enterprise 1.6.x or 1.7.x capabilities were imported.
- No database tables, columns, constraints, or seed data changed.
- No API routes or scopes changed.
- No authentication, authorization, findings, analytics, import, portfolio, roadmap, or repository behavior changed.
- Alembic head remains `0015_phase15`.

## Upgrade

OpenEA Community 1.5.1 installations can upgrade in place. Preserve the PostgreSQL data volume and `.env`, replace/rebuild the application, and allow the normal startup migration command to run. Since there is no new migration, the database remains at `0015_phase15 (head)`.

See `docs/upgrading.md` for the detailed procedure.

## Front-end dependency note

The 1.5.2 baseline still uses the pinned jsDelivr references inherited from 1.5.1 for Tabler Core, HTMX, Lucide, and Cytoscape.js. Bundling those pinned third-party assets locally is intentionally tracked as a separate Community maintenance enhancement so the baseline does not silently substitute or modify third-party artifacts.
