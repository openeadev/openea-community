# OpenEA Community Standard Metamodel — Phase 3

OpenEA Community 0.3.0 seeds twelve system object types:

- Business Product
- Business Capability
- Business Process
- Organization
- Role
- Application
- Application Service
- Data Object
- Technology
- Initiative / Project
- Architecture Principle
- Architecture Decision

Each `object_types` row includes a stable key, display name, architecture domain, description, and validated property-schema definition.

## Hybrid object model

The `objects` table contains commonly queried universal metadata such as name, description, record status, governance status, lifecycle stage, criticality, source, confidence, review dates, audit timestamps, and archival timestamp. Flexible object-specific fields are stored in `properties`, backed by JSONB on PostgreSQL.

The browser must never be allowed to store arbitrary JSON. `MetamodelService.validate_object_properties()` rejects unknown property keys, invalid data types, invalid enumerated values, malformed dates, malformed object UUID references, and missing required schema properties.

## Enumerations

Phase 3 seeds 21 governed enumeration definitions, including record/governance status, criticality, confidence, source, application and technology lifecycle values, fit values, strategic status, initiative status, decision status, and other standard reference data.

## Relationships

Phase 3 seeds 25 unique governed relationship types and 44 explicit valid source/target rules. One relationship type may be valid for several object-type pairs. The type stores both its forward label and inverse display label.

Example:

```text
Stored vocabulary: Application -> supports -> Business Capability
Inverse display:   Business Capability -> supported by -> Application
```

No inverse relationship record is defined or required.

`MetamodelService.validate_relationship_rule()` rejects unsupported source/target combinations. `integrates_with` also contains a governed property schema for integration type, protocol, direction, criticality, description, and data exchanged.

## Seeding

A normal `0003_phase3` migration seeds mandatory system metamodel data. The operation can also be rerun safely:

```bash
python -m app.cli seed-system
```

The seed service uses deterministic UUIDs and upsert-style behavior so repeated runs do not create duplicates.
