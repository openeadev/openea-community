# 9. Use Findings and Analytics

The Acme Bank repository now contains enough connected architecture data for OpenEA to do useful analysis. This chapter shows how deterministic metrics and findings turn repository conditions into explainable architecture work.

For formulas and score bands, use [Analytics and Repository Health](../../user-guide/analytics.md). For finding lifecycle and administration, use [Findings](../../user-guide/findings.md) and [Built-in Finding Rules](../../reference/finding-rules.md).

## Goal

You will:

- Force a synchronous metrics calculation so the tutorial has deterministic results.
- Evaluate all finding rules.
- Inspect the deliberately created Acme Bank problems.
- Trace findings back to repository data.
- Review repository health dimensions.
- Update a finding without changing the underlying architecture.

## 1. Make sure the worker is running

For a normal Docker Compose installation:

```bash
docker compose ps
```

The `worker` service should be running. Repository changes queue background calculation jobs, and the worker consumes those jobs. Platform Administrator schedules also queue periodic Analytics & Metrics and Findings Evaluation work so time-dependent conditions stay current when the repository is idle.

The tutorial uses the synchronous `*-now` commands below only to remove timing ambiguity while you follow the exercises; those commands are not the normal periodic scheduler.

For details, see [Worker and Background Calculations](../../administration/worker-jobs.md).

## 2. Recalculate metrics synchronously for the tutorial

Normally you can allow the worker to process queued jobs. For a hands-on tutorial, it is useful to remove timing ambiguity before evaluating findings.

From the OpenEA repository directory, run:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
```

You should see output similar to:

```text
Metrics recalculation complete: metrics=<number>
```

The exact number can vary if you added extra records. Do not use the count as a pass/fail test.

OpenEA Community 1.5.2 persists these metric types:

- `application_risk`
- `technology_risk`
- `capability_risk`
- `data_quality`
- `impact_severity`

Each score is deterministic and stores its components and explanation.

## 3. Evaluate findings

Use either the browser or CLI.

### Browser method

1. Select **Findings**.
2. Select **Evaluate findings**.
3. Allow the worker a few seconds to process the queued evaluation.
4. Refresh the Findings page if necessary.

### Synchronous CLI method

For deterministic tutorial timing:

```bash
docker compose exec web python -m app.cli evaluate-findings-now
```

The command reports the number of currently active findings.

The number is not expected to match this documentation exactly if your repository contains any additional objects, different review dates, or experiments from earlier chapters.

## 4. Find the Legacy Wire Transfer problems

Filter or scan the Findings workspace for **Legacy Wire Transfer**.

Based on the canonical tutorial model, you should expect findings corresponding to these built-in rules:

| Rule | Why the condition exists |
| --- | --- |
| `APP-OWNER-001` | Owner organization and owner role were deliberately left blank. |
| `APP-CAP-001` | No `supports → Business Capability` relationship was created. |
| `APP-FIT-001` | Technical Fit was deliberately left unset. |
| `APP-TECH-001` | The application uses Java 8, whose Strategic Status is `Retire`. |
| `APP-RETIRED-TECH-001` | The active application uses Java 8, whose lifecycle is `End of Support`. |
| `APP-RISK-001` | The application is Mission Critical and the calculated application risk can reach the rule threshold because of its technology exposure and data-quality gaps. |

Open one of the findings and read the stored evidence/explanation. The purpose is to verify that the finding can be traced back to repository facts.

!!! important "A finding is not the architecture"
    Changing a finding status does not change the underlying application, technology, relationship, owner, or lifecycle. The architecture repository remains authoritative. Findings are an operational layer derived from it.

## 5. Inspect the Java 8 finding

Find **Java 8**.

The canonical tutorial data has:

```text
Lifecycle stage: End of Support
Strategic Status: Retire
Vendor Support End: 2022-03-31
```

You should expect:

| Rule | Meaning |
| --- | --- |
| `TECH-EOS-001` | Vendor support end is in the past. |

Open Java 8 from the finding or through Explore and verify the repository values that caused it.

This is an example of an explainable architecture concern:

```text
Technology fact
Vendor Support End = 2022-03-31
        ↓
Deterministic rule
TECH-EOS-001
        ↓
Finding
Technology past end of support
```

## 6. Inspect business-capability coverage findings

Look for these capabilities:

### Regulatory Reporting

You intentionally created no supporting Application.

Expected rule:

```text
CAP-APP-001 — Capability has no application support
```

### Customer Management

You created exactly one supporting application: Digital Banking.

Expected rule:

```text
CAP-APP-002 — Capability has single application dependency
```

### Payments

You created exactly one supporting application: Payments Hub.

Expected rule:

```text
CAP-APP-002 — Capability has single application dependency
```

The finding does not state that a single supporting application is automatically wrong. It exposes concentration so an architect can decide whether the dependency is acceptable.

## 7. Inspect the Data Object finding

Find **Regulatory Report**.

You deliberately omitted a system-of-record relationship.

Expected rule:

```text
DATA-SOR-001 — Data object has no system of record
```

Compare that with:

- Customer → system of record is Core Banking
- Account → system of record is Core Banking
- Payment → system of record is Payments Hub

The relationship model, not a free-text note, drives this rule.

## 8. Inspect the overdue review finding

Find **Regulatory Reporting** again, this time for the review condition.

In the previous chapter you explicitly set:

```text
Next review date: 2026-01-01
```

Because that date is overdue, you should expect:

```text
REVIEW-001 — Architecture review overdue
```

Open **Regulatory Reporting → Lifecycle** and confirm the next review date shown there matches the evidence.

## 9. Expect missing-review-date findings too

OpenEA Community 1.5.2 also seeds:

```text
REVIEW-002 — Missing review date
```

This rule applies to significant architecture objects that have no `next_review_date`.

Many objects in this tutorial have a Review frequency of `Annual`, but you have not yet completed a review for them. A review frequency by itself does **not** populate the next review date. Therefore, you may see several `REVIEW-002` findings.

That is expected and is useful for understanding the difference between:

```text
Review policy: Annual
```

and:

```text
Scheduled next review: 2027-08-29
```

The exact number of `REVIEW-002` findings depends on which significant records you have already reviewed.

## 10. View metrics for an object

Open **Legacy Wire Transfer** and select **View Metrics**.

Review the available metric cards. Pay particular attention to:

- Application Risk
- Data Quality
- Impact Severity, when available

For each card, select **How is this calculated and what can I do?**. OpenEA expands the deterministic formula, component values, current inputs, missing/stale information, and recommended response. It also provides links back to the Object, Edit form, Relationships, Lifecycle, or Impact Analysis where those areas are relevant.

Do not focus only on the final 0–100 score. **Data Quality is better when higher; risk metrics are better when lower; Impact Severity is reach rather than a quality target.**

For user guidance see [Analytics and Repository Health](../../user-guide/analytics.md). For the exact 1.5.2 mappings and thresholds see [Metric Calculation Reference](../../reference/analytics-metrics.md).

## 11. Compare with Digital Banking

Open **Digital Banking → View Metrics**.

Digital Banking has more complete architecture context:

- Structured owner organization and role
- Business capability relationships
- Current strategic technologies
- Business, Technical, and Strategic Fit values
- Data relationships
- An accepted Architecture Decision affecting it

Compare its metrics with Legacy Wire Transfer. The tutorial is designed so the difference is explainable from repository content rather than from an opaque model.

## 12. Open the Analytics workspace

Select **Analytics** from the navigation.

OpenEA summarizes repository health across five dimensions:

- Completeness
- Freshness
- Ownership
- Relationship coverage
- Governance

Select each dimension and inspect the records below 100%.

You should be able to recognize Acme Bank conditions you created deliberately:

- Ownership gaps on Legacy Wire Transfer
- Missing expected relationships
- Missing/overdue review dates
- Many objects still in governance `Draft`

This is why repository health should be treated as a quality lens, not as a mysterious score.

## 13. Practice finding workflow without changing the architecture

Choose one noncritical tutorial finding, such as a single-application-dependency finding.

If your current authorization allows it, update its operational status to `Acknowledged` and optionally assign it.

Supported finding statuses in 1.5.2 are:

```text
Open
Acknowledged
Accepted
Remediation Planned
Resolved
Dismissed
```

If you choose `Dismissed`, OpenEA requires a dismissal reason.

After changing the finding status, reopen the related architecture object. Notice that nothing in the architecture record changed. This is intentional separation between:

```text
Architecture state
```

and:

```text
Finding workflow state
```

In Chapter 13, you will change the architecture itself and then evaluate findings again so OpenEA can resolve conditions that no longer exist.

## Checkpoint

You should now understand how OpenEA moves from structured repository facts to explainable analysis:

```text
Objects + relationships + lifecycle + ownership + review dates
                         ↓
                  Persisted metrics
                         ↓
                Deterministic rules
                         ↓
                      Findings
```

Continue to [Run Impact Analysis](09-impact-analysis.md).
