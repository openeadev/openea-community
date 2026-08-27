# Development Architecture

OpenEA Community intentionally uses a small server-rendered architecture.

## Application layers

Business responsibilities follow this direction:

```text
Routes
  ↓
Services
  ↓
Repositories / Data Access
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

Routes should remain presentation/transport oriented. Business validation belongs in services rather than templates or route handlers.

## Web architecture

The browser application uses:

- FastAPI
- Jinja2 server rendering
- HTMX for focused progressive enhancement
- Tabler/Bootstrap visual foundation
- Lucide icons
- Focused JavaScript modules
- Cytoscape.js for repository-derived graph visualization

OpenEA does not require a Node.js build pipeline or JavaScript SPA framework.

## Search

`SearchService` is the architecture-discovery boundary. PostgreSQL provides full-text and fuzzy search through `to_tsvector`, `websearch_to_tsquery`, and `pg_trgm` indexes.

## Impact

`ImpactService` performs cycle-safe recursive relationship traversal in PostgreSQL and returns repository objects plus relationship paths. It does not introduce a second graph database.

## Analytics and jobs

`AnalyticsService` persists deterministic metrics in `object_metrics`.

`JobService` uses PostgreSQL as a lightweight queue. The dedicated worker claims queued jobs and recalculates metrics/findings outside the web request.

## Consistent service layer

Browser routes, REST API writes, and CSV imports reuse the same business services. This prevents an import or API request from bypassing metamodel validation, relationship rules, auditing, or recalculation triggers.
