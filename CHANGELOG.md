# Changelog

## 1.5.2 - Independent Community baseline

- Fixed Impact Analysis query-filter parsing and clarified combined filter semantics while preserving explanatory path nodes.
- Added deterministic Attention reason explanations to the existing overdue Reviews workspace.
- Expanded object Metrics pages with formulas, components, current inputs, missing/stale conditions, remediation guidance, and direct navigation actions.
- Added a technical Metric Calculation Reference and improved Acme Bank tutorial callout formatting.

- Established OpenEA Community as an independently versioned distribution from OpenEA Enterprise.
- Renamed the Python distribution from `openea` to `openea-community`; the internal `app` import package remains unchanged for upgrade compatibility.
- Added `.env.example`, `.gitignore`, and `.dockerignore` for clean public-source and Docker packaging.
- Removed generated Python/cache/package metadata from the release archive.
- Replaced hard-coded UI release labels with the configured application version.
- Preserved 1.5.1 repository data and database-schema compatibility while applying 1.5.2 maintenance/UI fixes.
- No schema migration is required; Alembic head remains `0015_phase15`.
- Added MkDocs development commands to the Makefile for background preview, status, stop, and strict documentation builds, with corresponding README guidance.
- Grouped relationship choices alphabetically by relationship label and target object type.
- Filtered relationship target objects dynamically to the selected governed target type, sorted them alphabetically, and excluded archived records while retaining Draft, Active, and Inactive records.
- Extended relationship editing so permitted users can change the relationship type/target combination and target object while preserving the source object and metamodel validation.
- Added regression coverage for relationship choice ordering, target filtering, archived-target exclusion, and relationship type/target edits.

## 1.5.1 - Findings and repository-health UX

- Resolved findings are hidden by default from the operational Findings workspace while remaining available through status filtering.
- Added explicit Current, All statuses, and individual status filtering for historical findings.
- Added short explanatory info icons to all five Repository Health dimension cards.
- Made Repository Health dimension cards clickable and added object-level drill-down pages for Completeness, Freshness, Ownership, Relationship Coverage, and Governance.
- Drill-down pages show the objects reducing each score, the per-object score, and an explainable reason.
- No schema migration is required; Alembic head remains `0015_phase15`.

## 1.5.0 - Custom declarative finding rules

- Added Architecture Administrator UI for creating, editing, enabling/disabling, and deleting custom declarative finding rules.
- Added validated authoring for missing-field, date-threshold, missing-relationship, relationship-count, related-object-status, risk-threshold, review-overdue, and duplicate-name rules.
- Built-in rule identity/type/applicability remains protected; supported severity and threshold/value parameters can be tuned.
- Custom rule deletion is soft archival so historical findings and audit events remain available.
- Added rule creator/updater provenance and archived-at metadata via migration `0015_phase15`.
- Changed built-in seeding so administrator-tuned parameters are not overwritten on startup.
- Added audit events and automatic findings reevaluation for custom rule lifecycle actions.
- Added regression coverage for custom rule evaluation, arbitrary-rule rejection, soft deletion, built-in protection, and UI authorization.

## 1.4.0 - Relationship CSV import

- Added a separate relationship CSV upload/map/validate/preview/commit workflow.
- Added deterministic source/target resolution: UUID, external ID when available, exact name, then alias.
- Added ambiguity rejection rather than automatic guessing.
- Added relationship New/Update/Unchanged/Error preview classification.
- Added relationship metadata and governed property import.
- Added CSV Import audit source and batch correlation IDs.
- Added `0014_phase14` import-batch migration and regression coverage.


## 1.3.0 - API authentication

- Added user-managed Personal Access Tokens with scoped `/api/v1` Bearer authentication.
- Added Platform Administrator-managed non-interactive service accounts with independent OpenEA role assignments.
- Added token scopes, 30/60/90/180/365/Never expiration, one-time secret display, hash-only storage, last-used tracking, and revocation.
- Added Platform Administrator token inventory/revocation.
- Repaired Swagger UI CSP and exposed HTTP Bearer authentication in OpenAPI.
- Added migration `0013_phase13` for service-account identity flags and API tokens.
- Preserved the 1.2.0 Tabler UI and all repository functionality.

## 1.2.0 - Tabler UI rebranding

- Replaced the authenticated top-navigation shell with a responsive Tabler-based left application sidebar.
- Added browser-local light/dark theme selection with no server-side preference persistence.
- Redesigned the public landing page, login page, first-run setup, and dashboard.
- Added placeholder OpenEA mark, wordmark, and favicon assets for later replacement.
- Retained the blue/white OpenEA visual direction while improving spacing, navigation hierarchy, cards, forms, and responsive behavior.
- Pinned Tabler Core 1.4.0 from jsDelivr; no Node.js build chain is introduced.
- Carried forward the 1.1.0 Ruff cleanup to the demo, findings, and portfolio modules.
- No database migration or business-functionality changes are included.

## 1.1.0 - Fresh-install maintenance release

- Fixed clean PostgreSQL installation failure during Phase 3 metamodel seeding.
- Phase 3 migration now performs metamodel-only seeding and cannot invoke later finding-rule seed responsibilities.
- System seeding now checks whether `rule_definitions` exists before seeding finding rules.
- Added regression coverage for pre-Phase-10 seed behavior.
- No database schema changes; Alembic head remains `0012_phase12`.

## 1.0.0 - Phase 12

- Completed the OpenEA MVP.
- Added governed CSV upload, mapping, validation, preview, commit, and filtered export.
- Added versioned `/api/v1` objects, relationships, search, impact, findings, reviews, and analytics endpoints.
- Kept OpenAPI documentation functional at `/docs`.
- Added optional Northstar Financial demo data with idempotent seed and archival removal commands.
- Added Playwright live MVP workflow definitions.
- Added final API, import, backup/restore, integration, and development documentation.
- Added `0012_phase12` migration for persistent import batches.
- Improved Docker startup sequencing so migrations/system seeding finish before the worker starts.

## 0.11.0 - Phase 11

- Added Application Portfolio and TIME-style fit classification.
- Added Technology Portfolio with support horizon and dependent-application exposure.
- Added hierarchical Capability Map with repository/metric overlays.
- Added derived Roadmaps using structured architecture dates.
- Added Portfolio and Roadmaps primary navigation.
- Added Phase 11 release-marker Alembic migration and regression tests.

# Changelog

## 0.10.0 - Phase 10

- Added persisted Findings and Rule Definition models.
- Added sixteen built-in declarative finding rules covering lifecycle, ownership, relationships, reviews, risk, initiative collisions, and potential service duplication.
- Added finding lifecycle, assignment, resolution notes, and mandatory dismissal reasons.
- Added automatic finding deduplication and automatic resolution when conditions clear.
- Added audited finding status changes and Architecture Administrator rule enable/disable actions.
- Added Findings dashboard, finding detail/evidence view, and rule administration workspace.
- Extended the PostgreSQL-backed worker to evaluate finding rules asynchronously.
- Added migration `0010_phase10` without recreating existing repository data.
- Preserved Python 3.10 compatibility and all Phase 1–9 behavior.

## 0.9.0 - Phase 9

- Added persisted Application, Technology, Capability, Data Quality, and Impact Severity metrics.
- Added deterministic formulas with stored component/input explanations and risk bands.
- Added repository health and per-object analytics views.
- Added PostgreSQL-backed jobs plus a dedicated Docker worker process.
- Added automatic deduplicated recalculation jobs after relevant changes.
- Added migration `0009_phase9` without recreating existing repository data.
- Preserved Python 3.10 compatibility and all Phase 1–8 behavior.


## 0.8.0 - Phase 8

- Added cycle-safe recursive impact traversal with a default depth of 3 and maximum depth of 5.
- Added direct and indirect impact classification with object-type grouping.
- Added preserved relationship paths and inverse-label explanations for each impacted object.
- Added relationship-type traversal filters and object-type result filters.
- Added repository-derived Cytoscape.js impact graph with object navigation.
- Added Viewer-compatible read-only impact analysis.
- Added Alembic release marker `0008_phase8` with no destructive schema changes.
- Preserved Python 3.10 compatibility and all Phase 1-7 behavior.

## 0.7.0 - Phase 7

- Added governance transitions and dedicated Principle/Decision workflows.
- Added system-assigned ADR identifiers and decision superseding.
- Added review cycles, review history, and overdue-review workspace.
- Added comments and object activity/history tabs.
- Added immutable append-only audit events with before/after state.
- Added audit coverage for objects, relationships, reviews, comments, and user administration.
- Preserved Python 3.10 compatibility and all Phase 1–6 behavior.

## 0.6.0 — Phase 6: Search and Navigation

- Added PostgreSQL full-text search and `pg_trgm` fuzzy matching.
- Added alias/tag search, combined repository filters, sorting, result counts, and pagination.
- Added global authenticated search entry point.
- Added migration `0006_phase6` with required PostgreSQL search indexes.
- Added Phase 6 search and authorization regression tests.

## 0.5.0 — Phase 5: Relationships

- Added first-class architecture relationship records.
- Added governed relationship creation, editing, and archival.
- Added inbound/outbound relationship views with inverse labels.
- Added relationship metadata and validated relationship properties.
- Added server-side source/target rule enforcement and duplicate prevention.
- Added Phase 5 authorization and regression coverage.

## 0.4.0 — Phase 4: Repository UI

- Added Explore navigation and architecture object list/detail pages.
- Added schema-driven create/edit forms for all twelve standard object types.
- Added lifecycle, ownership, aliases, tags, source/confidence, filtering, and sorting.
- Added soft archival and server-side repository role enforcement.
- Added owner organization/role columns through Alembic migration `0004_phase4`.
- Added Phase 4 regression coverage while preserving Phase 1–3 behavior.

## 0.3.0 — Phase 3: Metamodel Foundation

- Added the 12 standard OpenEA architecture object types.
- Added relational universal object metadata plus JSONB object-specific properties.
- Added governed object-type schema definitions and server-side property validation.
- Added 21 standard enumeration definitions and their values.
- Added 25 standard relationship types with inverse labels and 44 valid source/target rules.
- Added relationship-property schema validation, including application integration metadata.
- Added object alias and tag persistence models.
- Added deterministic, idempotent system metamodel seeding and `seed-system` CLI command.
- Added Alembic migration `0003_phase3` with mandatory online system seed.
- Added metamodel validation and seed regression tests.
- Added the missing explicit `itsdangerous` Phase 2 runtime dependency.
- Preserved Python 3.10 minimum compatibility and all Phase 1/2 functionality.

## 0.2.0 — Phase 2: Identity and Authorization

- Added local user identities and five system application roles.
- Added Argon2id password hashing and local login/logout.
- Added browser and CLI initial Platform Administrator setup.
- Added signed HttpOnly SameSite sessions with HTTPS-aware Secure cookies.
- Added session-bound CSRF protection.
- Added server-side authentication and role authorization dependencies.
- Added Platform Administrator user-management UI and role assignment.
- Added temporary account lockout after repeated failed authentication.
- Added Alembic migration `0002_phase2` without recreating the database.
- Preserved Python 3.10 minimum compatibility and all Phase 1 functionality.

## 0.1.0 — Phase 1: Foundation

- Added FastAPI application foundation, PostgreSQL/SQLAlchemy/Alembic plumbing, configuration, logging, security headers, health/readiness endpoints, Jinja2/HTMX/Bootstrap UI shell, Docker Compose, tests, and project documentation.
- Corrected the baseline to support Python 3.10+.
