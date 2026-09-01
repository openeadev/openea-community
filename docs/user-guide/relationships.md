# Manage Relationships

Relationships connect architecture objects and are validated against the standard metamodel.

## Create a relationship

Architecture Administrators, Architects, and Contributors can create permitted relationships.

1. Open the source object.
2. Open **Relationships**.
3. Choose to add a relationship.
4. Select a valid relationship type and target object type combination.
5. Select the target object.
6. Add optional relationship metadata.
7. Save.

The relationship selector is grouped alphabetically by relationship label. When a relationship supports more than one target object type, those target types are listed alphabetically within the relationship group. For example, an Organization can show separate choices for `owns → Application`, `owns → Business Capability`, and `owns → Business Product`.

After you select the relationship combination, OpenEA loads only objects of the permitted target type. Target objects are sorted alphabetically by name. Archived objects are excluded; Draft, Active, and Inactive records remain eligible targets.

Changing the relationship selection clears the current target selection and reloads the valid targets for the new combination. This prevents a target selected for one metamodel rule from carrying over to an incompatible rule.

The service layer validates the source/type/target combination again before commit. The browser filtering is guidance, not the security or integrity boundary.


## Relationships to archived objects

Archiving an object does **not** delete or automatically archive its existing relationships. OpenEA preserves those relationship records because they explain historical architecture context and can become current again if the object is restored.

On an object's **Relationships** tab, current relationships are shown by default. Archived related objects and separately archived relationship records are hidden until you select **Show archived**. Select **Hide archived** to return to the current-state view.

When archived entries are shown, OpenEA keeps the normal theme-controlled table background in both light and dark mode and uses the red **Archived** badge as the visual status indicator. The single **Show archived** control reveals both relationships to archived objects and relationship records that were themselves archived. Historical relationship entries are read-only in this view.

The Relationships tab count reflects the entries currently displayed: it counts current relationships by default and includes historical entries after **Show archived** is selected. Existing relationship history remains stored, but an archived object is not eligible as the target of a new relationship. When an archived object is restored, its preserved relationships return to the current-state view automatically.

## Edit a relationship

Permitted users can edit both the governed relationship identity and its metadata while keeping the source object fixed.

Editable relationship identity fields are:

- Relationship type / target object type combination
- Target object

The same filtering rules used during creation apply during editing. The target list contains only non-archived objects that are valid for the selected relationship rule and is sorted alphabetically.

Editable relationship metadata includes:

- Description
- Criticality
- Confidence
- Validity dates
- Source
- Relationship-specific properties

If you change the relationship type, OpenEA validates the new type against the existing source object and the newly selected target object before saving. Relationship-specific properties are also validated against the newly selected relationship type.

OpenEA prevents an edit from producing a duplicate relationship with the same relationship type, source object, and target object.

## Archive a relationship

Architecture Administrators and Architects are authorized to archive relationships in the service/API layer. Contributors can create and edit relationships but cannot archive them.

!!! note "Browser UI in 1.5.2"
    The standard 1.5.2 Relationships table exposes **Edit** for a relationship but does not expose an **Archive** button. Use the supported API/administrative path when relationship archival is required.

## Duplicate prevention

OpenEA enforces one active relationship instance for a given relationship type, source object, and target object. Do not create separate inverse rows.

## Integration relationships

`Application integrates with Application` supports governed properties for integration context, including protocol, direction, criticality, description, and data exchanged.

## Bulk relationship creation

For larger data sets, use the separate [Relationship CSV Import](import-export.md) workflow rather than trying to embed relationship creation inside object CSV imports.
