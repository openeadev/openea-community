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

The **Reviews** workspace lists overdue active records and links directly to the Lifecycle tab for remediation.

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
