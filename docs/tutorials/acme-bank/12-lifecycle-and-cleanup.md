# 13. Edit, Remediate, Govern, and Archive

The previous chapters intentionally left architecture problems in Acme Bank. This final tutorial shows the normal maintenance lifecycle: edit records, improve ownership and relationships, complete reviews, apply governance transitions, reevaluate findings, inspect history, and archive a record.

For the generic object workflow, see [Manage Architecture Objects](../../user-guide/objects.md). For review/governance behavior, see [Reviews and Architecture Decisions](../../user-guide/reviews-decisions.md).

## Goal

You will:

- Correct structured ownership on CSV-imported Applications.
- Remediate several Legacy Wire Transfer data-quality findings.
- Complete a new Regulatory Reporting review.
- Move Digital Banking through normal governance approval.
- Recalculate metrics and reevaluate findings.
- Inspect immutable audit history.
- Archive the temporary Fraud Monitoring Application.

## 1. Add structured ownership to Regulatory Reporting Platform

Open **Regulatory Reporting Platform** and select **Edit**.

Set:

| Field | Value |
| --- | --- |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |

Leave the free-text Application properties as imported:

```text
Business Owner: Regulatory Reporting
Technical Owner: Regulatory Technology
```

Select **Save changes**.

The structured owner fields are the fields used by OpenEA's universal repository ownership model. The free-text business/technical owner properties remain useful application-specific context.

## 2. Add structured ownership to Fraud Monitoring

Open **Fraud Monitoring → Edit**.

Set:

| Field | Value |
| --- | --- |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |

Select **Save changes**.

After findings are reevaluated, the ownership conditions introduced by the CSV import should no longer apply to these two Applications.

## 3. Remediate Legacy Wire Transfer ownership and Technical Fit

Open **Legacy Wire Transfer → Edit**.

Change only these fields:

| Field | New value |
| --- | --- |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |
| Technical Fit | `Fair` |

Select **Save changes**.

Do **not** change its Java 8 dependency, lifecycle, or retirement initiative. Those remain real architecture concerns in this scenario.

This edit should remove the underlying conditions for:

- `APP-OWNER-001`
- `APP-FIT-001`

on the next findings evaluation.

## 4. Add a capability mapping for Legacy Wire Transfer

Open **Legacy Wire Transfer → Relationships → + Add relationship**.

Create:

```text
Legacy Wire Transfer → supports → Payments
```

Use:

```text
Confidence: High
Source: Manual
```

Select **Save relationship**.

This corrects the missing-capability condition (`APP-CAP-001`).

Notice that the architecture risk related to Java 8 is still present. Data-quality remediation does not pretend the obsolete runtime disappeared.

## 5. Complete a new review for Regulatory Reporting

Open **Regulatory Reporting → Lifecycle**.

The previous review deliberately scheduled `2026-01-01`, which is overdue.

In **Review notes**, enter:

```text
Completed Acme Bank tutorial remediation review. Application support is now documented through Regulatory Reporting Platform.
```

For **Next review date**, choose a date that is safely in the future relative to the day you perform the tutorial. For example, if you perform the tutorial on 2026-08-29, use:

```text
2027-08-29
```

Select **Mark reviewed**.

OpenEA appends a new Review history entry rather than overwriting the previous review record.

After findings are reevaluated, `REVIEW-001` should no longer apply while the new next-review date remains in the future.

## 6. Approve an ordinary architecture object through governance

So far you used specialized Principle and Decision status flows. Now use the standard governance workflow on **Digital Banking**.

Open **Digital Banking → Lifecycle**.

Its universal Governance status should still be `Draft` unless you changed it earlier.

OpenEA Community 1.5.2 uses these normal-object transitions:

```text
Draft → Submitted
Submitted → Approved | Rejected | Needs Review
Rejected → Draft
Needs Review → Submitted | Draft
Approved → Needs Review
```

For this tutorial:

1. Apply `Draft → Submitted`.
2. Apply `Submitted → Approved`.

The object now has an approved governance state without editing the disabled Governance status field on the normal Edit form.

This also demonstrates how governance can improve the repository-wide Governance health dimension.

## 7. Inspect history after your changes

Open **Legacy Wire Transfer → History**.

You should see audit events corresponding to changes such as object edits and relationship creation.

Open **Regulatory Reporting → Lifecycle** and inspect its Review history, then open its **History** tab to compare review history with general audit history.

OpenEA treats audit events as an immutable historical record of operations rather than an editable comment log.

Also inspect **Digital Banking → History** and locate governance-transition events generated by the approval workflow.

## 8. Recalculate metrics and findings

Run:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

Then return to **Findings**.

## 9. Verify which findings changed

### Legacy Wire Transfer

The following data-quality conditions should no longer be active after your remediation:

```text
APP-OWNER-001
APP-CAP-001
APP-FIT-001
```

However, these architecture concerns can remain because the application still uses Java 8:

```text
APP-TECH-001
APP-RETIRED-TECH-001
TECH-EOS-001 (on Java 8)
```

Depending on the recalculated score and threshold, high application risk may also remain.

This is desirable. Adding an owner and capability mapping improves data quality, but it does not erase technology obsolescence.

### Regulatory Reporting

The original no-application-support condition was removed by the CSV relationship import. Because Regulatory Reporting now has exactly one supporting Application, you may instead see the single-application-dependency signal.

The overdue-review condition should no longer be active after the new review date is scheduled in the future.

### Regulatory Report

The `DATA-SOR-001` condition should no longer be active because Regulatory Reporting Platform is now its system of record.

### Payments

Payments now has multiple supporting Applications:

- Payments Hub
- Fraud Monitoring
- Legacy Wire Transfer, after the remediation relationship

Therefore, the single-supporting-application condition should no longer apply.

## 10. Find resolved findings

OpenEA 1.5.2 hides resolved findings from the default current-findings view.

Use the status filtering on **Findings** to include or select `Resolved` and inspect findings whose underlying conditions no longer exist.

This lets you preserve operational history while keeping the default workspace focused on current conditions.

## 11. Edit a relationship's metadata

Open **Legacy Wire Transfer → Relationships**.

Find the `supports → Payments` relationship you just created and select **Edit**.

Add a Description such as:

```text
Legacy wire processing contributes to the Payments capability until retirement is complete.
```

Set **Criticality** to `High` and save the relationship.

This demonstrates that relationship metadata can evolve without changing the relationship's source, type, or target identity.

!!! note "Relationship archival in the 1.5.2 browser"
    OpenEA Community 1.5.2 has relationship archival support in the service/API layer for authorized users, but the standard Relationships table exposes **Edit** rather than an Archive button. Do not expect a browser Archive action for a relationship in this version.

## 12. Archive Fraud Monitoring

**Fraud Monitoring** was introduced primarily to teach the CSV workflow. Use it now to practice object archival.

1. Open **Fraud Monitoring**.
2. Review its Relationships tab so you know what context exists.
3. Select **Archive** in the object header.
4. Confirm the browser prompt:

   ```text
   Archive this architecture object?
   ```

OpenEA performs a soft archive:

- `archived_at` is populated.
- Record status becomes `Archived`.
- An `ObjectArchived` audit event is recorded.
- Existing relationships are preserved.
- Metrics recalculation is queued.

The record is no longer treated as a current repository object by normal search or analysis.

!!! important "Archive is not hard delete"
    Archiving preserves historical architecture context. OpenEA's repository-first/history principles favor archival over destructive deletion where practical. Related objects continue to show the preserved relationship with an **Archived** marker, and users can show or hide archived related objects on the Relationships tab.

### Find the archived record

1. Return to **Explore**.
2. In **Record status**, choose **Archived**.
3. Confirm **Fraud Monitoring** appears with an Archived marker.
4. Open the record and review the archived-record notice.

The record remains readable, including its History and preserved Relationships.

### Optional: practice Restore

If you want to practice restoration before continuing:

1. On the archived **Fraud Monitoring** record, select **Restore**.
2. Confirm the record returns to its pre-archive Record Status.
3. Confirm its relationships are still present.
4. Archive **Fraud Monitoring** again so the canonical tutorial state remains unchanged.

## 13. Recalculate after archival

Run again:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

Return to:

- **Application Portfolio**
- **Capability Map**
- **Findings**

Observe how derived views change when an object is no longer active.

For example, after Fraud Monitoring is archived and assuming Legacy Wire Transfer still supports Payments, Payments retains more than one supporting active Application. If you later archive Legacy Wire Transfer too, the supporting-application count will change again.

## 14. Do not prematurely retire Legacy Wire Transfer in the canonical scenario

The repository currently says:

```text
Legacy Wire Retirement
└── retires → Legacy Wire Transfer

Legacy Wire Transfer
└── Planned Retirement Date: 2027-06-30
```

That represents a planned future state. Do not set Actual Retirement Date or archive the application merely to make the risk findings disappear before the retirement actually occurs.

This is an important architecture-governance principle: OpenEA should describe reality and approved plans, not manipulate data to improve dashboard scores.

When the application is genuinely retired, a normal closeout could include:

1. Edit Application lifecycle to `Retired`.
2. Enter the actual retirement date.
3. Update or archive obsolete relationships as appropriate through supported workflows/API.
4. Complete the retirement initiative.
5. Recalculate metrics and evaluate findings.
6. Archive the application record when your repository policy calls for it.

## 15. Final Acme Bank model review

You have now exercised every standard OpenEA object type and the major Community 1.5.2 workflows:

- Create architecture objects manually
- Edit objects
- Use aliases and tags
- Build governed relationships
- Edit relationship metadata
- Track organizational ownership and role accountability
- Model business capabilities and processes
- Model application services
- Model data and systems of record
- Model technologies and support horizons
- Model initiatives and retirement plans
- Create and approve an Architecture Principle
- Create and accept an Architecture Decision
- Perform reviews
- Transition ordinary governance status
- Run metrics
- Evaluate and manage findings
- Run Impact Analysis
- Use Application and Technology Portfolios
- Use Capability Map overlays
- Use derived Roadmaps
- Import objects with CSV
- Import relationships with CSV
- Inspect audit history
- Archive an architecture object

## The architecture you built

The central value is not the number of records. It is the traceability between them.

For example:

```text
Consumer Banking
   ↓ requires
Deposit Account Management
   ↑ supports
Digital Banking
   ├── uses → Java 21
   ├── uses → PostgreSQL 17
   ├── uses → Kubernetes
   ├── reads → Customer
   └── reads → Account
          ↑
          │ system of record for
     Core Banking
```

and:

```text
Prefer Strategic Technologies
           ▲
           │ conforms to
Standardize Digital Channels on Java 21
           │
           ├── selects → Java 21
           ├── affects → Digital Banking
           └── affects → Digital Banking Modernization
```

and the legacy-risk path:

```text
Legacy Wire Retirement
        │ retires
        ▼
Legacy Wire Transfer
        │ uses
        ▼
      Java 8
        │
        └── End of Support / Retire
```

That is the repository-first model OpenEA is designed to support.

## Where to go next

Use the Acme Bank repository as a sandbox for the standalone tutorials and reference sections:

- [Manage Architecture Objects](../../user-guide/objects.md)
- [Manage Relationships](../../user-guide/relationships.md)
- [Impact Analysis](../../user-guide/impact-analysis.md)
- [Findings](../../user-guide/findings.md)
- [Portfolios and Roadmaps](../../user-guide/portfolios-roadmaps.md)
- [CSV Import and Export](../../user-guide/import-export.md)
- [API v1](../../reference/api.md)
- [Built-in Finding Rules](../../reference/finding-rules.md)

For production administration, continue with the [Administration](../../administration/users-permissions.md) documentation rather than treating tutorial values as production policy.
