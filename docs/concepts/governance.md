# Governance and History

OpenEA separates the lifecycle of an architecture object from its governance state.

An Application can be lifecycle `Active` while its governance status is `Draft`, `Approved`, or `Needs Review`.

## General governance flow

The standard governance workflow is:

```text
Draft ──► Submitted ──► Approved
  ▲           │             │
  │           ├──► Rejected │
  │           └──► Needs Review ◄──┘
  └──────── Rejected / Needs Review
```

Supported transitions are validated server-side.

## Architecture Principles

Principles use their own status model:

```text
Draft → Proposed → Approved → Deprecated → Retired
```

A Proposed principle can also return to Draft.

## Architecture Decisions

Architecture Decisions use ADR-style statuses:

- Draft
- Proposed
- Accepted
- Rejected
- Superseded
- Deprecated
- Expired

OpenEA assigns decision identifiers such as `ADR-0001`. The display identifier is separate from the object's UUID.

An Accepted decision can supersede another decision through the governed `supersedes` relationship.

## Reviews

Objects can have review frequencies of Monthly, Quarterly, Semiannual, or Annual. A Contributor, Architect, or Architecture Administrator can mark a record reviewed, enter notes, and specify the next review date.

If an explicit next date is not provided, OpenEA derives it from the review frequency.

The **Reviews** workspace lists overdue active records.

## Comments and audit history

Comments are collaboration records attached to an architecture object. They are not architecture objects and do not participate in the relationship graph.

Significant writes generate audit events containing actor, action, entity, time, source, and before/after state where applicable. PostgreSQL protects the audit-event table with an immutable-table trigger that rejects updates and deletes.
