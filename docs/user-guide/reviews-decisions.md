# Reviews and Architecture Decisions

OpenEA combines periodic review tracking with ADR-style Architecture Decision records.

## Reviews

An architecture object can have a review frequency of:

- Monthly
- Quarterly
- Semiannual
- Annual

Contributors, Architects, and Architecture Administrators can mark a record reviewed from its Lifecycle area.

A review can include:

- Notes
- Explicit next review date

If no explicit next date is supplied, OpenEA derives one from the object's review frequency.

## Reviews workspace

The **Reviews** workspace preserves the OpenEA Community 1.5.2 scope: it lists non-archived records whose explicit **Next Review Date** is in the past.

The **Attention reason** column explains why each row needs attention. The overdue date is always shown, and OpenEA also adds applicable review context such as:

- no completed review has been recorded
- Governance Status is `Needs Review`
- Confidence is `Unknown` or `Low`

These additional reasons explain the row; they do not broaden the workspace to records that are not already overdue.

Select the object name to open its Lifecycle tab, where an authorized reviewer can record a new review and schedule the next date.

## Architecture Decisions

Architecture Decisions are repository objects with fields for:

- Decision number
- Context
- Decision
- Rationale
- Alternatives considered
- Consequences
- Decision status
- Decision/effective/review dates
- Decision owner
- Approving body
- Exception expiration

OpenEA assigns a display identifier such as `ADR-0001`.

!!! info "Decision number and initial status are controlled"
    The Decision Number is generated automatically. New Architecture Decisions are created in `Draft`; use the Lifecycle workflow for later status transitions.

## Decision lifecycle

The normal decision flow is:

```text
Draft → Proposed → Accepted
              └──► Rejected
```

Additional terminal or later-life states include Superseded, Deprecated, and Expired.

## Superseding a decision

To supersede an existing decision:

1. Create or identify the replacement Architecture Decision.
2. Move the replacement to `Accepted`.
3. From the older decision, choose the accepted replacement.
4. OpenEA creates `replacement → supersedes → old decision`.
5. The older decision transitions to `Superseded`.

This preserves why an earlier decision existed while making the current decision clear.
