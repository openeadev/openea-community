# Analytics and Risk

OpenEA Community 0.9.0 adds deterministic, persisted architecture analytics. Risk and impact remain separate: risk measures how concerning an object is, while impact severity estimates architecture reach. Every persisted metric stores its formula, component scores, inputs, and calculation timestamp.

## Persisted metric types

- `application_risk`
- `technology_risk`
- `capability_risk`
- `data_quality`
- `impact_severity`

All scores are integers from 0–100. Bands are Low (0–24), Moderate (25–49), High (50–74), and Critical (75–100).

## Application Risk

Application Risk follows the documented weighted model: Technology Risk 30%, Technical Fit 20%, Lifecycle Risk 15%, Dependency Risk 15%, Data Quality Risk 10%, and Review Freshness 10%. The weighted score is multiplied by Criticality (Low 0.75, Medium 1.00, High 1.15, Mission Critical 1.30) and capped at 100.

Technology exposure uses the highest persisted risk among technologies directly related through `Application -> uses -> Technology`; it is not averaged, so a single high-risk dependency remains visible.

## Technology Risk

Technology Risk uses Vendor Lifecycle 30%, Internal Strategy 30%, Support Horizon 25%, Review Freshness 10%, and Data Quality Risk 5%. Strategic-status and support-horizon mappings follow the master specification.

## Capability Risk

Capability Risk uses Supporting Application Risk 40%, Technology Exposure 20%, Application Redundancy 10%, Single Point of Failure 15%, Capability Maturity 10%, and Data Quality Risk 5%. Multiple supporting applications are treated only as an overlap/rationalization signal; OpenEA does not automatically declare them redundant.

## Data Quality

Data Quality uses Required Fields 30%, Recommended Fields 15%, Ownership 15%, Relationship Coverage 20%, Review Freshness 15%, and Source Confidence 5%. The explanation records missing or stale items so the score is actionable rather than opaque.

## Impact Severity

Impact Severity uses the existing repository traversal at depth 3. Components are Direct Dependents 25%, Critical Dependents 25%, Business Reach 20%, Dependency Depth 15%, and Strategic Importance 15%. The numeric value supplements—not replaces—the impact paths introduced in Phase 8.

## Background recalculation

Phase 9 activates OpenEA's PostgreSQL-backed job queue. Writes that can materially affect metrics enqueue one deduplicated `recalculate_all_metrics` job. The worker claims jobs with `SELECT ... FOR UPDATE SKIP LOCKED` on PostgreSQL and recalculates persisted metrics outside the web request.

Docker Compose now runs `web`, `worker`, and `postgres`. No Redis, Celery, RabbitMQ, Kafka, or external queue is required.

Administrative commands:

```bash
python -m app.cli recalculate-metrics
python -m app.cli recalculate-metrics-now
```

The first command queues normal worker processing. The second performs a synchronous recalculation for administrative verification and troubleshooting.

## Repository health

`/analytics` summarizes average Data Quality plus completeness, freshness, ownership, relationship coverage, and governance coverage. It also shows the current highest Application, Technology, and Capability risks. `/analytics/objects/{uuid}` exposes each persisted score and its component-level explanation.


## Repository Health drill-downs

Beginning with 1.5.1, the five Repository Health dimensions are explainable from the dashboard. Each card includes a concise definition and links to `/analytics/health/<dimension>`. The drill-down lists every active repository object scoring below 100% for that dimension, its object-level score, and the reason it is reducing the repository percentage.

- **Completeness**: required fields defined by the object's metamodel schema.
- **Freshness**: next-review and last-reviewed dates using the same review-freshness calculation as Data Quality.
- **Ownership**: owner organization, owner role, or recognized object-specific owner properties.
- **Relationship coverage**: expected governed relationship types for the object's type.
- **Governance**: active records in `Approved` or `Accepted` governance states.
