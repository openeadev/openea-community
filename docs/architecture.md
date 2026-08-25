# Architecture

OpenEA Community 0.9.0 remains a single FastAPI web application backed by PostgreSQL and rendered with Jinja2/Bootstrap, with HTMX available for focused progressive enhancement. Business responsibilities remain separated as Routes → Services → Repositories/Data Access → SQLAlchemy/PostgreSQL.

## Phase 6 search layer

`SearchService` is the query boundary for architecture discovery. PostgreSQL provides authoritative search using `to_tsvector`/`websearch_to_tsquery` and `pg_trgm`; no external search engine is required. Search indexes cover object names/descriptions plus trigram indexes for names, aliases, and tags. The service owns filtering, ranking, sorting, and pagination so routes/templates remain presentation-oriented.

The abstraction intentionally leaves room to add external identifiers when the external-reference model is introduced later without changing the Explore route contract.


## Phase 7 governance layer

Governance, review, comments, and audit behavior is implemented through dedicated services. Audit events are appended in the same database transaction as the business change. PostgreSQL additionally protects `audit_events` with an immutable-table trigger. Architecture Decision identifiers remain separate from UUIDs.


## Phase 8 impact layer

Impact analysis remains inside the service layer. `ImpactService` builds a recursive relationship traversal over PostgreSQL, tracks visited object IDs per path to prevent cycles, retains the relationship/object path used to reach each result, and returns repository objects rather than introducing a second graph database. The UI renders those results server-side and provides a focused Cytoscape.js visualization derived from the same result data. No graph layout is authoritative or persisted.


## Phase 9 analytics and worker layer

`AnalyticsService` calculates deterministic metrics and persists them in `object_metrics`; page requests read persisted results rather than recalculating complex analytics. `JobService` uses PostgreSQL as a lightweight queue. The dedicated worker claims queued jobs using row locks and `SKIP LOCKED`, recalculates metrics, and records job state. The web and worker remain parts of one deployable codebase and share the same service layer; no message broker or distributed-event infrastructure is introduced.

## 1.0 MVP completion

The browser UI and `/api/v1` share the same service layer. CSV import also commits through `ObjectService`; it cannot bypass metamodel validation, auditing, or metric recalculation. Import preview state is stored in PostgreSQL (`import_batches`). PostgreSQL remains the authoritative repository.

The production process model is PostgreSQL + web + worker. On Docker startup, the web service completes Alembic migration and idempotent system seeding before becoming healthy; the worker starts only after web readiness. Background metrics and findings use the PostgreSQL-backed `jobs` table with row locking rather than an external broker.
