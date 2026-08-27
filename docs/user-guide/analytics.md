# Analytics and Repository Health

OpenEA persists deterministic architecture metrics so expensive analysis does not have to be recalculated on every page request.

## Metric types

OpenEA Community 1.5.2 calculates:

- `application_risk`
- `technology_risk`
- `capability_risk`
- `data_quality`
- `impact_severity`

Scores range from 0 to 100 and use these bands:

| Score | Band |
| --- | --- |
| 0–24 | Low |
| 25–49 | Moderate |
| 50–74 | High |
| 75–100 | Critical |

Each persisted metric includes its score, band, calculation time, component values, inputs, and explanation.

## Application Risk

Application Risk combines:

- Technology Risk — 30%
- Technical Fit — 20%
- Lifecycle Risk — 15%
- Dependency Risk — 15%
- Data Quality Risk — 10%
- Review Freshness — 10%

The weighted result is adjusted by criticality and capped at 100. Direct technology exposure uses the highest persisted risk among Technologies linked through `Application → uses → Technology`.

## Technology Risk

Technology Risk combines:

- Vendor Lifecycle — 30%
- Internal Strategy — 30%
- Support Horizon — 25%
- Review Freshness — 10%
- Data Quality Risk — 5%

## Capability Risk

Capability Risk combines:

- Supporting Application Risk — 40%
- Technology Exposure — 20%
- Application Redundancy signal — 10%
- Single Point of Failure — 15%
- Capability Maturity — 10%
- Data Quality Risk — 5%

Multiple supporting applications are treated as a rationalization signal, not an automatic declaration that they are redundant.

## Data Quality

Data Quality combines:

- Required fields — 30%
- Recommended fields — 15%
- Ownership — 15%
- Relationship coverage — 20%
- Review freshness — 15%
- Source confidence — 5%

The explanation identifies missing or stale elements so the result is actionable.

## Repository Health

The **Analytics** workspace summarizes five repository-wide dimensions:

- **Completeness** — required metamodel fields
- **Freshness** — review freshness
- **Ownership** — recognized accountable ownership
- **Relationship coverage** — expected governed relationship types
- **Governance** — active records in Approved or Accepted governance states

Select a dimension to see every active object below 100% for that measure and the reason it reduces the repository score.

## Background recalculation

Relevant repository changes queue a deduplicated metrics-recalculation job in PostgreSQL. The worker processes the job outside the web request. See [Worker and Background Calculations](../administration/worker-jobs.md).
