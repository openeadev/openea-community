# Standard Metamodel

OpenEA Community 1.5.2 seeds twelve system object types and 21 governed enumerations. The metamodel is used by browser forms, CSV import, API validation, relationship validation, analytics, and findings.

## Universal object metadata

All architecture objects share repository fields for name, description, record status, governance status, lifecycle, criticality, owner organization, owner role, source, confidence, validity dates, review dates/frequency, aliases, tags, timestamps, and archival state.

## Object types

### Business Product

A product or service offered by the enterprise.

**Domain:** Business  
**Key:** `business_product`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `product_type` | `text` | No |  |
| `business_owner` | `text` | No |  |
| `customer_segment` | `text` | No |  |
| `strategic_importance` | `text` | No |  |
| `lifecycle_stage` | `select` | No | `Planned`, `Active`, `Sunset`, `Retired` |
| `launch_date` | `date` | No |  |
| `retirement_date` | `date` | No |  |

### Business Capability

An ability the enterprise requires to achieve outcomes.

**Domain:** Business  
**Key:** `business_capability`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `capability_level` | `integer` | No |  |
| `parent_capability` | `object_reference` | No | Object reference: `business_capability` |
| `business_owner` | `text` | No |  |
| `maturity` | `select` | No | `Initial`, `Developing`, `Defined`, `Managed`, `Optimized` |
| `target_maturity` | `select` | No | `Initial`, `Developing`, `Defined`, `Managed`, `Optimized` |
| `strategic_importance` | `text` | No |  |

### Business Process

A structured business process.

**Domain:** Business  
**Key:** `business_process`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `parent_process` | `object_reference` | No | Object reference: `business_process` |
| `process_owner` | `text` | No |  |
| `frequency` | `text` | No |  |
| `business_criticality` | `select` | No | `Low`, `Medium`, `High`, `Mission Critical` |
| `automation_level` | `select` | No | `Manual`, `Mostly Manual`, `Hybrid`, `Mostly Automated`, `Automated` |
| `lifecycle_stage` | `select` | No | `Planned`, `Active`, `Changing`, `Retiring`, `Retired` |

### Organization

An internal or external organizational unit.

**Domain:** Business  
**Key:** `organization`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `organization_type` | `select` | No | `Enterprise`, `Division`, `Business Unit`, `Department`, `Team`, `External Organization` |
| `parent_organization` | `object_reference` | No | Object reference: `organization` |
| `organization_code` | `text` | No |  |
| `external_organization` | `boolean` | No |  |

### Role

An architecture or business responsibility role, separate from OpenEA authorization roles.

**Domain:** Business  
**Key:** `role`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `role_type` | `text` | No |  |
| `organization` | `object_reference` | No | Object reference: `organization` |
| `responsibilities` | `long_text` | No |  |

!!! info "Role organization versus Owner organization"
    The `organization` property above is the Role's organizational placement: the organization the role belongs to or operates within. The universal **Owner organization** field is separate repository metadata describing stewardship of the OpenEA record. The two references may point to the same Organization or to different Organizations.

### Application

A deployable or acquired software application relevant to enterprise architecture.

**Domain:** Application  
**Key:** `application`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `application_type` | `text` | No |  |
| `business_owner` | `text` | No |  |
| `technical_owner` | `text` | No |  |
| `lifecycle_stage` | `select` | No | `Proposed`, `Planned`, `Development`, `Active`, `Tolerated`, `Sunset`, `Retired` |
| `business_fit` | `select` | No | `Poor`, `Fair`, `Good`, `Excellent`, `Unknown` |
| `technical_fit` | `select` | No | `Poor`, `Fair`, `Good`, `Excellent`, `Unknown` |
| `strategic_fit` | `select` | No | `Poor`, `Fair`, `Good`, `Excellent`, `Unknown` |
| `hosting_model` | `text` | No |  |
| `delivery_model` | `text` | No |  |
| `vendor` | `text` | No |  |
| `product_name` | `text` | No |  |
| `version` | `text` | No |  |
| `go_live_date` | `date` | No |  |
| `planned_retirement_date` | `date` | No |  |
| `actual_retirement_date` | `date` | No |  |
| `replacement_application` | `object_reference` | No | Object reference: `application` |
| `rto_hours` | `decimal` | No |  |
| `rpo_hours` | `decimal` | No |  |
| `data_classification` | `select` | No | `Public`, `Internal`, `Confidential`, `Restricted` |
| `internet_facing` | `boolean` | No |  |

### Application Service

A logical function exposed or provided by an application.

**Domain:** Application  
**Key:** `application_service`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `service_type` | `text` | No |  |
| `service_owner` | `text` | No |  |
| `lifecycle_stage` | `select` | No | `Proposed`, `Active`, `Deprecated`, `Retired` |
| `availability_requirement` | `text` | No |  |
| `consumer_type` | `text` | No |  |

### Data Object

Logical business information rather than a physical database table.

**Domain:** Information  
**Key:** `data_object`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `data_domain` | `text` | No |  |
| `data_owner` | `text` | No |  |
| `data_steward_role` | `object_reference` | No | Object reference: `role` |
| `classification` | `select` | No | `Public`, `Internal`, `Confidential`, `Restricted` |
| `retention_requirement` | `text` | No |  |
| `personally_identifiable` | `boolean` | No |  |
| `regulated` | `boolean` | No |  |

### Technology

An architectural technology product or platform, not an operational instance.

**Domain:** Technology  
**Key:** `technology`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `technology_category` | `text` | No |  |
| `vendor` | `text` | No |  |
| `product` | `text` | No |  |
| `version` | `text` | No |  |
| `lifecycle_stage` | `select` | No | `Emerging`, `Current`, `Aging`, `End of Support`, `Retired` |
| `strategic_status` | `select` | No | `Adopt`, `Strategic`, `Tolerate`, `Contain`, `Migrate`, `Retire` |
| `vendor_support_end` | `date` | No |  |
| `extended_support_end` | `date` | No |  |
| `internal_support_end` | `date` | No |  |
| `replacement_technology` | `object_reference` | No | Object reference: `technology` |
| `approved_for_new_use` | `boolean` | No |  |

### Initiative / Project

A change initiative or project affecting architecture.

**Domain:** Change  
**Key:** `initiative`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `initiative_type` | `text` | No |  |
| `sponsor` | `text` | No |  |
| `owning_organization` | `object_reference` | No | Object reference: `organization` |
| `architecture_owner` | `text` | No |  |
| `status` | `select` | No | `Idea`, `Proposed`, `Approved`, `In Progress`, `On Hold`, `Completed`, `Cancelled` |
| `start_date` | `date` | No |  |
| `target_end_date` | `date` | No |  |
| `actual_end_date` | `date` | No |  |
| `strategic_priority` | `text` | No |  |
| `delivery_health` | `select` | No | `Green`, `Amber`, `Red`, `Unknown` |
| `architecture_engagement_status` | `select` | No | `Not Required`, `Not Started`, `Assessment`, `Design`, `Review`, `Approved`, `Exception Required`, `Complete` |

### Architecture Principle

A durable principle guiding architecture decisions.

**Domain:** Governance  
**Key:** `architecture_principle`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `statement` | `long_text` | Yes |  |
| `rationale` | `long_text` | No |  |
| `implications` | `long_text` | No |  |
| `category` | `text` | No |  |
| `status` | `select` | No | `Draft`, `Proposed`, `Approved`, `Deprecated`, `Retired` |
| `effective_date` | `date` | No |  |
| `review_date` | `date` | No |  |
| `owner` | `text` | No |  |

### Architecture Decision

An ADR-style architecture decision.

**Domain:** Governance  
**Key:** `architecture_decision`

| Property | Type | Required | Governed values / target |
| --- | --- | --- | --- |
| `decision_number` | `text` | No |  |
| `context` | `long_text` | Yes |  |
| `decision` | `long_text` | Yes |  |
| `rationale` | `long_text` | No |  |
| `alternatives_considered` | `long_text` | No |  |
| `consequences` | `long_text` | No |  |
| `decision_status` | `select` | No | `Draft`, `Proposed`, `Accepted`, `Rejected`, `Superseded`, `Deprecated`, `Expired` |
| `decision_date` | `date` | No |  |
| `effective_date` | `date` | No |  |
| `review_date` | `date` | No |  |
| `decision_owner` | `text` | No |  |
| `approving_body` | `text` | No |  |
| `exception_expiration` | `date` | No |  |

## Governed enumerations

### Record Status

Key: `record_status`

`Draft`, `Active`, `Inactive`, `Archived`

`Archived` is the soft archive state. Archived objects retain identity, metadata, audit history, and existing relationships but are excluded from normal current-state analysis and new relationship target selection. They can be searched explicitly and restored by authorized users.

### Governance Status

Key: `governance_status`

`Draft`, `Submitted`, `Approved`, `Rejected`, `Needs Review`

### Criticality

Key: `criticality`

`Low`, `Medium`, `High`, `Mission Critical`

### Confidence

Key: `confidence`

`Unknown`, `Low`, `Medium`, `High`, `Confirmed`

### Source

Key: `source`

`Manual`, `Imported`, `External authoritative system`, `Discovered`, `Calculated`

### Business Product Lifecycle

Key: `business_product_lifecycle`

`Planned`, `Active`, `Sunset`, `Retired`

### Capability Maturity

Key: `capability_maturity`

`Initial`, `Developing`, `Defined`, `Managed`, `Optimized`

### Process Automation

Key: `process_automation`

`Manual`, `Mostly Manual`, `Hybrid`, `Mostly Automated`, `Automated`

### Business Process Lifecycle

Key: `business_process_lifecycle`

`Planned`, `Active`, `Changing`, `Retiring`, `Retired`

### Organization Type

Key: `organization_type`

`Enterprise`, `Division`, `Business Unit`, `Department`, `Team`, `External Organization`

### Application Lifecycle

Key: `application_lifecycle`

`Proposed`, `Planned`, `Development`, `Active`, `Tolerated`, `Sunset`, `Retired`

### Fit

Key: `fit`

`Poor`, `Fair`, `Good`, `Excellent`, `Unknown`

### Application Service Lifecycle

Key: `application_service_lifecycle`

`Proposed`, `Active`, `Deprecated`, `Retired`

### Data Classification

Key: `data_classification`

`Public`, `Internal`, `Confidential`, `Restricted`

### Technology Lifecycle

Key: `technology_lifecycle`

`Emerging`, `Current`, `Aging`, `End of Support`, `Retired`

### Technology Strategic Status

Key: `technology_strategy`

`Adopt`, `Strategic`, `Tolerate`, `Contain`, `Migrate`, `Retire`

### Initiative Status

Key: `initiative_status`

`Idea`, `Proposed`, `Approved`, `In Progress`, `On Hold`, `Completed`, `Cancelled`

### Delivery Health

Key: `delivery_health`

`Green`, `Amber`, `Red`, `Unknown`

### Architecture Engagement

Key: `architecture_engagement`

`Not Required`, `Not Started`, `Assessment`, `Design`, `Review`, `Approved`, `Exception Required`, `Complete`

### Architecture Principle Status

Key: `principle_status`

`Draft`, `Proposed`, `Approved`, `Deprecated`, `Retired`

### Architecture Decision Status

Key: `decision_status`

`Draft`, `Proposed`, `Accepted`, `Rejected`, `Superseded`, `Deprecated`, `Expired`
