# Governance, Reviews, Audit, and Comments

OpenEA Community separates architecture lifecycle from governance state. An Application can, for example, be lifecycle `Active` while governance status is `Approved`.

## General governance

The general governed flow is intentionally small:

- Draft → Submitted
- Submitted → Approved, Rejected, or Needs Review
- Rejected → Draft
- Needs Review → Submitted or Draft
- Approved → Needs Review

Governance state changes are performed from the object's Lifecycle tab and are validated server-side.

## Architecture Principles

Principle states are:

Draft → Proposed → Approved → Deprecated → Retired

A Proposed principle can also be returned to Draft.

## Architecture Decisions

Decision states are:

- Draft
- Proposed
- Accepted
- Rejected
- Superseded
- Deprecated
- Expired

Normal acceptance flow is Draft → Proposed → Accepted. A Proposed decision can be rejected or returned to Draft. An Accepted decision may be superseded by another accepted Architecture Decision using the governed `supersedes` relationship.

Architecture Decisions receive an OpenEA Community display identifier such as `ADR-0001`. This value is separate from the object's UUID and is not user-editable.

## Reviews

Objects may have a review frequency of Monthly, Quarterly, Semiannual, or Annual. A user with Contributor, Architect, or Architecture Administrator privileges can mark a record reviewed, enter review notes, and provide an explicit next review date. If no explicit next date is supplied, OpenEA Community derives one from the configured review frequency.

The Reviews workspace lists overdue active records.

## Comments

Comments are collaboration records attached to an architecture object. They are not architecture objects and do not participate in the relationship graph.

## Audit history

Significant repository writes create audit events containing the actor, action, entity, timestamp, source, and before/after state where applicable. Relationship activity also creates object-level activity entries so object History pages explain changes to their architecture context.

The PostgreSQL `audit_events` table is append-only. A database trigger rejects UPDATE and DELETE operations against audit rows.
