# API v1 Reference

OpenEA Community exposes a versioned REST API under:

```text
/api/v1
```

Interactive Swagger UI is available at `/docs`, and the OpenAPI schema is `/openapi.json`.

## Authentication

API requests can use an authenticated OpenEA browser session or a Bearer token:

```http
Authorization: Bearer openea_pat_<prefix>_<secret>
```

Bearer-token requests must satisfy both application-role authorization and the token's endpoint scope.

## Core scopes

- `objects:read`, `objects:write`
- `relationships:read`, `relationships:write`
- `search:read`
- `impact:read`
- `findings:read`, `findings:write`
- `reviews:read`, `reviews:write`
- `analytics:read`

## Endpoints

### Objects

```text
GET    /api/v1/objects
POST   /api/v1/objects
GET    /api/v1/objects/{object_id}
PATCH  /api/v1/objects/{object_id}
DELETE /api/v1/objects/{object_id}
POST   /api/v1/objects/{object_id}/restore
```

Object list supports object type, record status, criticality, page, per-page, and `archive_scope` filters. `archive_scope` is one of `current` (default), `archived`, or `all`. `record_status=Archived` also searches archived records for backward-friendly behavior. `DELETE` performs soft archival; `POST .../restore` restores the object and preserves its existing relationships. Object payloads include `archived_at`.

### Relationships

```text
GET    /api/v1/relationships
POST   /api/v1/relationships
GET    /api/v1/relationships/{relationship_id}
PATCH  /api/v1/relationships/{relationship_id}
DELETE /api/v1/relationships/{relationship_id}
```

When `object_id` is supplied to the relationship list endpoint, `include_archived_related=false` hides relationships whose other endpoint is an archived object. The default is `true` so preserved historical context remains visible.

`PATCH /api/v1/relationships/{relationship_id}` can update relationship metadata and can optionally change `relationship_key` and `target_object_id`. The source object remains fixed. Any new relationship type/target combination must be valid for the source object under the governed metamodel, the target must be non-archived, and duplicate relationships are rejected.

### Search

```text
GET /api/v1/search?q=...&archive_scope=current
```

Search defaults to current records. Set `archive_scope=archived` to search only archived records or `archive_scope=all` to search both current and archived records.

### Impact

```text
GET /api/v1/impact/{object_id}?depth=3
```

Depth is restricted to 1–5. The response includes root data, direct results, indirect results, path details, and graph payload.

### Findings

```text
GET   /api/v1/findings
PATCH /api/v1/findings/{finding_id}
```

### Reviews

```text
GET  /api/v1/reviews
POST /api/v1/reviews/{object_id}
```

### Analytics

```text
GET /api/v1/analytics
GET /api/v1/analytics/objects/{object_id}
```

## Example

```bash
curl \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  https://architecture.example.com/api/v1/objects
```

A token with only `objects:read` receives `403` when used against an object-write endpoint.

## Service-layer consistency

API writes use the same ObjectService and RelationshipService paths as browser operations. They do not bypass metamodel validation, audit behavior, authorization, or background recalculation triggers.
