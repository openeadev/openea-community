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

### Owner organization and type-specific organization fields

**Owner organization** is universal repository metadata. It identifies the organization accountable for stewardship of the OpenEA record. It does not necessarily describe where the real-world object sits organizationally.

Some object types also have a type-specific organization reference. In particular, a **Role** has a **Role organization** field in the Role details section. That field identifies the organization the business or architecture role belongs to or operates within.

The two values are intentionally independent and may be the same or different. For example:

```text
Chief Security Officer
├── Owner organization → Enterprise Architecture
└── Role organization  → GIS
```

This means Enterprise Architecture stewards the repository record while the Chief Security Officer role belongs to GIS. It is also valid to set both fields to `GIS` when GIS both owns the repository record and contains the role.

## Edit an object

Architecture Administrators, Architects, and Contributors can edit existing objects.

Aliases are comma-separated alternative names. OpenEA treats duplicate aliases case-insensitively when processing form input, so values such as `GIS-Security` and `gis-security` represent the same alias and are stored only once. Existing unchanged aliases are preserved when unrelated fields are edited.

A Contributor can maintain records but cannot create or archive them.

## Archive and restore an object

Architecture Administrators and Architects can archive repository objects.

Archival is soft: the object receives an archival timestamp and its Record Status becomes `Archived` rather than being destructively deleted. Existing relationships are preserved so the historical architecture remains explainable.

Archived objects are excluded from normal repository search, analytics, findings, portfolios, roadmaps, impact analysis, and new relationship target lists. They remain directly viewable and are clearly marked as archived.

Use **Explore → Record status → Archived** to search archived records. **All records** searches current and archived records together. Open an archived record and select **Restore** to return it to the current repository. OpenEA restores the Record Status that the object had immediately before archival when that history is available; the safe fallback for older records without that audit context is `Inactive`.

Restoring an object does not recreate its relationships. The original relationship records were preserved during archival and become current-context relationships again automatically when the object is restored.

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
