# Manage Relationships

Relationships connect architecture objects and are validated against the standard metamodel.

## Create a relationship

Architecture Administrators, Architects, and Contributors can create permitted relationships.

1. Open the source object.
2. Open **Relationships**.
3. Choose to add a relationship.
4. Select a valid relationship type.
5. Select the target object.
6. Add optional relationship metadata.
7. Save.

The UI only offers combinations that make sense for the source object, and the service layer validates the source/type/target combination again before commit.

## Edit relationship metadata

Permitted users can edit metadata such as:

- Description
- Criticality
- Confidence
- Validity dates
- Source
- Relationship-specific properties

The source object, target object, and relationship type define the identity of the relationship and are not silently converted into another relationship during metadata editing.

## Archive a relationship

Architecture Administrators and Architects can archive relationships. Contributors can create and edit relationships but cannot archive them.

## Duplicate prevention

OpenEA enforces one active relationship instance for a given relationship type, source object, and target object. Do not create separate inverse rows.

## Integration relationships

`Application integrates with Application` supports governed properties for integration context, including protocol, direction, criticality, description, and data exchanged.

## Bulk relationship creation

For larger data sets, use the separate [Relationship CSV Import](import-export.md) workflow rather than trying to embed relationship creation inside object CSV imports.
