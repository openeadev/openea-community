# Metric Calculation Reference

This page documents the deterministic OpenEA Community 1.5.2 metric formulas implemented by `AnalyticsService`. It is the technical reference for interpreting persisted object metrics.

## Persistence and recalculation

Metrics are stored in `object_metrics` with:

- `object_id`
- `metric_type`
- `score`
- `band`
- JSON `explanation`
- `calculated_at`

Relevant repository writes enqueue a deduplicated background recalculation job. The worker recalculates Data Quality first because the risk formulas can depend on it.

All numeric scores are rounded and bounded to 0–100.

## Persisted bands

OpenEA 1.5.2 stores the following generic band with persisted metrics:

| Score | Persisted band |
| --- | --- |
| 0–24 | Low |
| 25–49 | Moderate |
| 50–74 | High |
| 75–100 | Critical |

For risk and impact metrics, higher values represent greater concern or reach. **Data Quality is different: higher Data Quality is better**, so use the score and component explanation rather than interpreting its generic persisted band as a risk label.

## Common lookup values

### Technical Fit risk

| Technical Fit | Risk value |
| --- | ---: |
| Excellent | 0 |
| Good | 20 |
| Fair | 50 |
| Poor | 80 |
| Unknown or unrecognized | 40 |

### Application lifecycle risk

| Lifecycle | Risk value |
| --- | ---: |
| Proposed | 10 |
| Planned | 10 |
| Development | 15 |
| Active | 10 |
| Tolerated | 50 |
| Sunset | 80 |
| Retired | 100 |
| Unrecognized value | 40 |

### Technology strategic-status risk

| Strategic Status | Risk value |
| --- | ---: |
| Adopt | 0 |
| Strategic | 5 |
| Tolerate | 30 |
| Contain | 50 |
| Migrate | 75 |
| Retire | 100 |
| Missing value defaults to Tolerate | 30 |

### Technology lifecycle risk

| Lifecycle | Risk value |
| --- | ---: |
| Emerging | 0 |
| Current | 5 |
| Aging | 50 |
| End of Support | 100 |
| Retired | 100 |
| Unrecognized value | 30 |

### Criticality multiplier

| Criticality | Multiplier |
| --- | ---: |
| Low | 0.75 |
| Medium | 1.00 |
| High | 1.15 |
| Mission Critical | 1.30 |

### Capability maturity risk

| Maturity | Risk value |
| --- | ---: |
| Initial | 100 |
| Developing | 75 |
| Defined | 50 |
| Managed | 25 |
| Optimized | 0 |
| Missing/unrecognized | 50 |

### Confidence score used by Data Quality

| Confidence | Quality value |
| --- | ---: |
| Unknown | 20 |
| Low | 40 |
| Medium | 60 |
| High | 80 |
| Confirmed | 100 |

## Review freshness

OpenEA first calculates a review-freshness **risk**:

- explicit Next Review Date in the past: `100`
- Next Review Date within 30 days: `60`
- Next Review Date within 31–90 days: `20`
- Next Review Date more than 90 days away: `0`
- no Next Review Date, but reviewed within 180 days: `20`
- no Next Review Date, last reviewed 181–365 days ago: `60`
- no Next Review Date, last reviewed more than 365 days ago: `100`
- no completed review and no Next Review Date: `75`

Data Quality converts this to a quality component as `100 - review freshness risk`. Risk metrics use the risk value directly.

## Vendor support horizon risk

For Technology Risk, Vendor Support End is converted to:

| Time until support end | Risk value |
| --- | ---: |
| Date missing | 30 |
| Already expired | 100 |
| Less than 6 months | 85 |
| 6 to less than 12 months | 60 |
| 12 to less than 24 months | 30 |
| 24 to less than 36 months | 10 |
| 36 months or more | 0 |

## Data Quality

Formula:

```text
required fields 30%
+ recommended fields 15%
+ ownership 15%
+ relationship coverage 20%
+ review freshness 15%
+ source confidence 5%
```

Required fields come from the selected Object Type's schema definition.

Recommended fields in 1.5.2 are:

| Object type | Recommended fields |
| --- | --- |
| Application | Technical Fit, Business Fit, Strategic Fit, Hosting Model |
| Technology | Strategic Status, Vendor Support End, Vendor, Product |
| Business Capability | Maturity, Strategic Importance |

Other object types have no additional recommended-field list and therefore receive 100 for that component.

Ownership scores 100 when the object has an Owner organization, Owner role, or a recognized object-specific owner property (`business_owner`, `technical_owner`, `service_owner`, `process_owner`, `data_owner`, `decision_owner`, or `owner`). Otherwise it scores 0.

Expected relationship coverage is:

| Object type | Expected relationship keys |
| --- | --- |
| Application | `supports`, `uses` |
| Business Capability | `supports` |
| Business Process | `supports`, `realizes` |
| Data Object | `system_of_record_for` |
| Technology | none; coverage is 100 |

Coverage is the percentage of expected relationship keys present on active relationships connected to the object.

The metric explanation also records missing required/recommended fields plus Owner, Current review, and Expected relationships when those conditions reduce quality.

## Technology Risk

Formula:

```text
vendor lifecycle 30%
+ internal strategy 30%
+ support horizon 25%
+ review freshness 10%
+ data quality risk 5%
```

`data quality risk = 100 - Data Quality score`.

The explanation stores the current Lifecycle, Strategic Status, and Vendor Support End date.

## Application Risk

Formula before criticality:

```text
technology risk 30%
+ technical fit 20%
+ lifecycle risk 15%
+ dependency risk 15%
+ data quality risk 10%
+ review freshness 10%
```

The weighted result is multiplied by the Criticality multiplier and then bounded to 0–100.

Technology Risk is the highest persisted `technology_risk` among Technologies connected by an active outbound `Application → uses → Technology` relationship. If no such persisted metric exists, the technology-risk input defaults to 30.

Dependency risk counts active outbound `depends_on` relationships:

| Dependency count | Risk value |
| --- | ---: |
| 0 | 0 |
| 1–2 | 25 |
| 3–5 | 50 |
| 6 or more | 75 |

The explanation stores Technical Fit, Lifecycle, dependency count, material Technology count, and criticality multiplier.

## Capability Risk

Formula:

```text
supporting application risk 40%
+ technology exposure 20%
+ application redundancy signal 10%
+ single point of failure 15%
+ capability maturity 10%
+ data quality risk 5%
```

Supporting applications are active Applications with an active outbound `supports` relationship to the Business Capability.

Supporting Application Risk uses the highest persisted Application Risk. If there are no supporting Applications, this input is 100. If supporting Applications exist but no persisted Application Risk is available, it defaults to 40.

Technology Exposure is the highest Technology Risk found through the supporting Applications' active `uses` relationships.

Application redundancy signal:

| Supporting applications | Signal |
| --- | ---: |
| 0 | 100 |
| 1 | 0 |
| 2–3 | 30 |
| 4 or more | 60 |

Single Point of Failure is 100 only when exactly one supporting Application exists; otherwise it is 0.

These are deterministic signals for investigation. They do not prove duplication or mandate an additional Application.

## Impact Severity

Impact Severity runs an unfiltered depth-3 Impact Analysis and calculates:

```text
direct dependents 25%
+ critical dependents 25%
+ business reach 20%
+ dependency depth 15%
+ strategic importance 15%
```

Signals are calculated as follows:

- Direct dependents: `min(100, direct result count × 20)`
- Critical dependents: `min(100, High/Mission Critical result count × 25)`
- Business reach: `min(100, unique Business-domain result count × 20)`
- Dependency depth: depth 0 = 0, depth 1 = 25, depth 2 = 60, depth 3 = 100
- Strategic importance: 100 when `strategic_importance` is High/Critical/Mission Critical; otherwise 50 when object Criticality is High/Mission Critical; otherwise 20

Impact Severity is not a remediation score. It identifies architectural reach that may require stronger change coordination and analysis.

## User-facing explanations

The **View Metrics** page renders the persisted formula, components, current inputs, missing/stale items, and deterministic remediation guidance. The UI links back to the Object, Edit form, Relationships, Lifecycle, and Impact Analysis where those are the relevant places to investigate or correct the repository state.
