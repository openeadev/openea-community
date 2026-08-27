# Built-in Finding Rules

OpenEA Community 1.5.2 seeds sixteen built-in declarative finding rules. Built-in rules cannot be deleted. Architecture Administrators can tune supported operational parameters such as severity, date windows, count bounds, risk thresholds, and configured related-status values.

| Rule ID | Severity | Name | Rule type | Description |
| --- | --- | --- | --- | --- |
| `TECH-EOS-001` | Critical | Technology past end of support | `date_threshold` | Technology vendor support date is past. |
| `TECH-EOS-002` | High | Technology approaching end of support | `date_threshold` | Technology vendor support ends within 180 days. |
| `APP-TECH-001` | High | Application uses retiring technology | `related_object_status` | Application uses technology marked Migrate or Retire. |
| `APP-OWNER-001` | High | Application has no owner | `missing_field` | Application has no owner organization or owner role. |
| `APP-CAP-001` | Medium | Application has no capability mapping | `missing_relationship` | Application does not support a Business Capability. |
| `CAP-APP-001` | High | Capability has no application support | `relationship_count` | Business Capability has no supporting Application. |
| `CAP-APP-002` | Medium | Capability has single application dependency | `relationship_count` | Business Capability has exactly one supporting Application. |
| `APP-SVC-DUP-001` | Medium | Potential application-service duplication | `duplicate_name` | Multiple active Application Services share the same normalized name and may require rationalization review. |
| `DATA-SOR-001` | High | Data object has no system of record | `relationship_count` | Data Object has no system of record. |
| `DATA-SOR-002` | High | Conflicting systems of record | `relationship_count` | Data Object has multiple systems of record. |
| `REVIEW-001` | Medium | Architecture review overdue | `review_overdue` | Architecture review date is overdue. |
| `APP-RISK-001` | Critical | High-risk mission-critical application | `risk_threshold` | Mission Critical Application has high or critical Application Risk. |
| `INIT-COLLISION-001` | Medium | Initiative change collision | `relationship_count` | Architecture object is being changed by multiple active initiatives. |
| `APP-RETIRED-TECH-001` | Critical | Active application linked to retired technology | `related_object_status` | Active Application uses retired Technology. |
| `APP-FIT-001` | Low | Missing technical fit | `missing_field` | Application technical fit is missing. |
| `REVIEW-002` | Low | Missing review date | `missing_field` | Significant architecture object has no next review date. |

## Supported custom rule types

- `missing_field`
- `date_threshold`
- `missing_relationship`
- `relationship_count`
- `related_object_status`
- `risk_threshold`
- `review_overdue`
- `duplicate_name`

Custom rules are validated against the active metamodel and receive stable IDs such as `CUSTOM-0001`. Archiving a custom rule disables it without destroying historical findings or audit events.