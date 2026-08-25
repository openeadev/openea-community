# API

OpenEA Community 1.3.0 exposes versioned REST endpoints under `/api/v1`. Interactive Swagger UI is available at `/docs`; the schema is `/openapi.json`.

## Authentication

API requests support either an authenticated OpenEA browser session or a Bearer token:

```http
Authorization: Bearer openea_pat_<prefix>_<secret>
```

Personal Access Tokens are owned by normal users and inherit that user's application roles. Service-account tokens are owned by non-interactive service accounts whose roles are assigned by a Platform Administrator. A service account cannot use the password/browser login flow.

Token secrets are generated with cryptographically secure randomness, stored only as SHA-256 hashes, and displayed once at creation. Tokens support 30, 60, 90, 180, 365 day expiration or Never, plus explicit revocation and last-used tracking.

## Scopes

Bearer requests must satisfy both the owner's OpenEA application role and the token scope required by the endpoint. Available scopes are:

- `objects:read`, `objects:write`
- `relationships:read`, `relationships:write`
- `search:read`
- `impact:read`
- `findings:read`, `findings:write`
- `reviews:read`, `reviews:write`
- `analytics:read`

A token can never grant more authority than the owner's assigned application roles.

Users manage their own PATs at `/account/tokens`. Platform Administrators create and manage service accounts at `/admin/service-accounts` and can review/revoke all tokens at `/admin/api-tokens`.

## Example

```bash
curl -H 'Authorization: Bearer YOUR_TOKEN' \
  http://localhost:8000/api/v1/objects
```

A token with only `objects:read` receives `403` if used against an object-write endpoint.

## Core endpoints

- `GET/POST /api/v1/objects`
- `GET/PATCH/DELETE /api/v1/objects/{uuid}`
- `GET/POST /api/v1/relationships`
- `GET/PATCH/DELETE /api/v1/relationships/{uuid}`
- `GET /api/v1/search?q=...`
- `GET /api/v1/impact/{uuid}?depth=3`
- `GET/PATCH /api/v1/findings`
- `GET /api/v1/reviews`
- `POST /api/v1/reviews/{object_uuid}`
- `GET /api/v1/analytics`
- `GET /api/v1/analytics/objects/{uuid}`

Object and relationship writes use the same service-layer validation, metamodel rules, and audit behavior as browser writes.
