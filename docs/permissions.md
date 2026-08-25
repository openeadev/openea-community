# Permissions

OpenEA Community application authorization roles are separate from architecture `Role` objects in the repository.

Phase 4 repository permissions are:

| Application role | Browse/detail | Create | Edit | Archive |
| --- | --- | --- | --- | --- |
| Platform Administrator | Yes | No* | No* | No* |
| Architecture Administrator | Yes | Yes | Yes | Yes |
| Architect | Yes | Yes | Yes | Yes |
| Contributor | Yes | No | Yes | No |
| Viewer | Yes | No | No | No |

`*` Platform Administrator is intentionally not an automatic architecture-governance superuser. Assign Architecture Administrator or Architect when that person also needs repository write permissions.

Phase 4 Contributor permission is role-level. More granular assignment/stewardship restrictions remain a later authorization evolution and are not simulated by UI-only controls.

## Import and API permissions in 1.0

CSV import is restricted to Architecture Administrators and Architects. CSV export is read-only and available to authenticated users. `/api/v1` read operations are available to Viewer, Contributor, Architect, and Architecture Administrator roles. Object creation/archive requires Architect or Architecture Administrator; Contributor can update existing objects and maintain permitted relationships. All authorization is enforced in route dependencies and service validation remains authoritative.

## API authorization (1.3.0)

Bearer tokens do not bypass OpenEA roles. Each `/api/v1` request must satisfy both the identity's application role and the token scope required by the endpoint. Personal tokens inherit the user's roles. Service accounts have independently assigned application roles and cannot log into the browser UI. Only Platform Administrators can create/manage service accounts.
