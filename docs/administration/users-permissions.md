# Users and Permissions

OpenEA Community uses local user identities and five system application roles.

Application roles are separate from architecture `Role` objects stored in the repository.

## Roles

- Platform Administrator
- Architecture Administrator
- Architect
- Contributor
- Viewer

A user can have more than one application role.

## Repository permissions

| Application role | Browse/detail | Create objects | Edit objects | Archive objects |
| --- | --- | --- | --- | --- |
| Platform Administrator | Yes | No* | No* | No* |
| Architecture Administrator | Yes | Yes | Yes | Yes |
| Architect | Yes | Yes | Yes | Yes |
| Contributor | Yes | No | Yes | No |
| Viewer | Yes | No | No | No |

`*` Platform Administrator is intentionally not an automatic architecture-governance superuser. Assign Architecture Administrator or Architect as an additional role when required.

## Relationship permissions

- Architecture Administrator: create, edit, archive
- Architect: create, edit, archive
- Contributor: create and edit
- Viewer: read only

## Governance and reviews

Architecture Administrators and Architects can perform governance transitions.

Architecture Administrators, Architects, and Contributors can:

- Mark objects reviewed
- Add review notes
- Add comments
- Update findings within permitted routes

## Import

Only Architecture Administrators and Architects can use CSV imports.

## Platform administration

Only Platform Administrators can:

- Create and manage normal users
- Create and manage service accounts
- Review/revoke all API tokens
- Configure periodic analytics and findings schedules
- Queue Analytics & Metrics or Findings Evaluation with **Run now**

Only Architecture Administrators can manage Finding Rules.

## API permissions

Bearer-token authorization is the intersection of:

1. The identity's OpenEA application roles
2. The token's requested scopes

A token cannot grant authority the identity does not already have.

Read-only API roles are Architecture Administrator, Architect, Contributor, and Viewer. Platform Administrator alone is not treated as a repository API role.
