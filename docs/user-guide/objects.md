# Manage Architecture Objects

OpenEA uses schema-driven forms for all twelve standard object types.

## Create an object

Users with the **Architect** or **Architecture Administrator** role can create objects.

1. Open **Explore**.
2. Select **New**.
3. Choose an object type.
4. Complete the common repository fields and type-specific properties.
5. Save the record.

OpenEA validates the object against the metamodel before committing it.

## Common fields

Typical fields include:

- Name and description
- Record status
- Governance status
- Lifecycle stage
- Criticality
- Owner Organization / Owner Role
- Source and confidence
- Validity dates
- Review frequency
- Aliases and tags

The object type determines which additional fields appear.

## Edit an object

Architecture Administrators, Architects, and Contributors can edit existing objects.

A Contributor can maintain records but cannot create or archive them.

## Archive an object

Architecture Administrators and Architects can archive repository objects.

Archival is soft: the object receives an archival timestamp rather than being destructively deleted. This preserves architecture history and audit context.

## Detail tabs

An object detail page can expose areas such as:

- Overview
- Relationships
- Visualize
- Lifecycle
- History
- Comments

The exact content depends on object type and available data.

## Good repository practice

For useful downstream analysis, prioritize:

1. Correct object type
2. Clear name and description
3. Ownership
4. Lifecycle and criticality
5. Relevant business and technology relationships
6. Review cadence
7. Source and confidence

A perfectly complete object with no relationships often provides less architectural value than a moderately complete object that is connected to the enterprise context around it.
