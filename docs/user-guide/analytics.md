# Analytics and Repository Health

OpenEA Community persists deterministic architecture metrics so expensive analysis does not have to be recalculated on every page request. Metrics are derived from repository facts; they are not manually entered ratings and should not be treated as targets to game.

## Metric types

OpenEA Community 1.5.2 calculates:

- `application_risk`
- `technology_risk`
- `capability_risk`
- `data_quality`
- `impact_severity`

Every persisted metric contains:

- the current 0–100 score
- the persisted band
- the exact formula description
- component values used by the formula
- current input values where applicable
- missing or stale items when the metric can identify them
- the calculation timestamp

For the exact mappings, thresholds, and formulas, see [Metric Calculation Reference](../reference/analytics-metrics.md).

## Reading the scores correctly

The direction of the score depends on the metric.

| Metric | How to read the score |
| --- | --- |
| Application Risk | Lower is better. Higher means more architecture concern. |
| Technology Risk | Lower is better. Higher means more lifecycle/support/strategy concern. |
| Capability Risk | Lower is better. Higher means more application, technology, resilience, maturity, or data-quality concern. |
| Data Quality | **Higher is better.** Low values mean the repository record is incomplete, stale, weakly owned, weakly connected, or low-confidence. |
| Impact Severity | Not a quality score. Higher means the object has broader or more significant architectural reach. |

!!! warning "Do not optimize the repository for the score"
    Change architecture data only when it reflects reality or stronger evidence. For example, do not delete a valid dependency simply to reduce Application Risk or Impact Severity. Correct the architecture first; then update OpenEA to describe the corrected state.

## Use View Metrics on an object

Open an architecture object and select **View Metrics**.

Each metric card shows the current score and a short explanation. Select **How is this calculated and what can I do?** to expand the deterministic details.

The expanded section shows:

1. **Current calculation** — the formula used by OpenEA.
2. **Components** — the 0–100 values feeding the formula.
3. **Current inputs** — values such as lifecycle, technical fit, support end date, dependency count, or supporting-application count.
4. **Missing / stale** — repository conditions OpenEA can identify directly.
5. **How to respond** — architecture actions that can improve the condition or help interpret the metric.
6. **Navigation links** — direct links to the object, edit form, Relationships, Lifecycle, or Impact Analysis where relevant.

## Application Risk

Application Risk combines:

- Technology Risk — 30%
- Technical Fit — 20%
- Lifecycle Risk — 15%
- Dependency Risk — 15%
- Data Quality Risk — 10%
- Review Freshness — 10%

The weighted result is adjusted by the application's criticality multiplier and capped at 100. Direct technology exposure uses the highest persisted Technology Risk among Technologies linked through `Application → uses → Technology`.

Typical remediation paths include:

- replacing or upgrading a high-risk Technology
- improving Technical Fit through an actual architecture change
- reviewing Sunset/Tolerated lifecycle conditions
- reducing unnecessary `depends on` coupling
- completing missing ownership, fields, relationships, or review information
- completing a current architecture review

Criticality is not something to lower merely to improve the metric. It should remain an accurate business property.

## Technology Risk

Technology Risk combines:

- Vendor Lifecycle — 30%
- Internal Strategy — 30%
- Support Horizon — 25%
- Review Freshness — 10%
- Data Quality Risk — 5%

Typical responses include:

- verify Lifecycle and Strategic Status
- set an accurate Vendor Support End date
- plan upgrade, migration, containment, or retirement before support expires
- complete a current review
- improve the Technology record's ownership, evidence, and required/recommended information

## Capability Risk

Capability Risk combines:

- Supporting Application Risk — 40%
- Technology Exposure — 20%
- Application Redundancy signal — 10%
- Single Point of Failure — 15%
- Capability Maturity — 10%
- Data Quality Risk — 5%

The redundancy signal is not proof that applications are duplicates. Likewise, a single supporting application is a concentration signal that may or may not require another application. Use the metric to investigate resilience and rationalization rather than treating the numeric value as a target.

## Data Quality

Data Quality combines:

- Required fields — 30%
- Recommended fields — 15%
- Ownership — 15%
- Relationship coverage — 20%
- Review freshness — 15%
- Source confidence — 5%

For Data Quality, **higher scores are better**.

The expanded metric view identifies missing or stale items. Common actions are:

- populate missing required or recommended fields
- assign an Owner organization or Owner role
- add the expected governed relationships that accurately describe the object
- complete or schedule a current review
- increase Confidence only when stronger evidence supports the record

## Impact Severity

Impact Severity uses a depth-3 repository traversal and combines:

- Direct dependents — 25%
- Critical dependents — 25%
- Business reach — 20%
- Dependency depth — 15%
- Strategic importance — 15%

A high Impact Severity score does **not** mean the object is bad. A central payment platform, shared data object, or strategic capability can legitimately have high impact.

Use the score to decide where change coordination, testing, recovery planning, and stakeholder engagement deserve more attention. Validate the underlying relationships and criticality values; only reduce dependencies when that is a real architecture improvement.

## Repository Health

The **Analytics** workspace summarizes five repository-wide dimensions:

- **Completeness** — required metamodel fields
- **Freshness** — review freshness
- **Ownership** — recognized accountable ownership
- **Relationship coverage** — expected governed relationship types
- **Governance** — active records in Approved or Accepted governance states

Select a dimension to see every non-archived object below 100% for that measure and the deterministic reason it reduces the repository score.

## Background recalculation

Relevant repository changes queue a deduplicated metrics-recalculation job in PostgreSQL. The worker processes the job outside the web request. See [Worker and Background Calculations](../administration/worker-jobs.md).
