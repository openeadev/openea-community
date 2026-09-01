# Relationship Vocabulary

OpenEA Community 1.5.2 seeds 25 governed relationship types. A relationship is valid only for the source/target combinations listed below. Inverse labels are display semantics; OpenEA stores one relationship row rather than a duplicate inverse row.

| Key | Forward label | Inverse label | Valid source → target |
| --- | --- | --- | --- |
| `requires` | requires | required by | Business Product → Business Capability |
| `realizes` | realizes | realized by | Business Process → Business Capability |
| `owns` | owns | owned by | Organization → Business Product<br>Organization → Business Capability<br>Organization → Application |
| `performs` | performs | performed by | Organization → Business Process |
| `participates_in` | participates in | has participant | Role → Business Process |
| `accountable_for` | accountable for | accountable role/organization | Role → Business Capability<br>Role → Application<br>Organization → Data Object |
| `supports` | supports | supported by | Application → Business Capability<br>Application → Business Process<br>Application Service → Business Process |
| `provides` | provides | provided by | Application → Application Service |
| `depends_on` | depends on | depended on by | Application → Application<br>Technology → Technology<br>Initiative / Project → Initiative / Project |
| `integrates_with` | integrates with | integrates with | Application → Application |
| `creates` | creates | created by | Application → Data Object |
| `reads` | reads | read by | Application → Data Object |
| `updates` | updates | updated by | Application → Data Object |
| `system_of_record_for` | system of record for | system of record | Application → Data Object |
| `uses` | uses | used by | Business Process → Data Object<br>Application → Technology<br>Application Service → Technology |
| `standardizes` | standardizes | standardized by | Organization → Technology |
| `changes` | changes | changed by | Initiative / Project → Application<br>Initiative / Project → Business Process |
| `introduces` | introduces | introduced by | Initiative / Project → Application<br>Initiative / Project → Technology |
| `retires` | retires | retired by | Initiative / Project → Application<br>Initiative / Project → Technology |
| `improves` | improves | improved by | Initiative / Project → Business Capability |
| `conforms_to` | conforms to | conformed to by | Architecture Decision → Architecture Principle<br>Application → Architecture Principle<br>Technology → Architecture Principle |
| `deviates_from` | deviates from | deviated from by | Architecture Decision → Architecture Principle<br>Application → Architecture Principle |
| `affects` | affects | affected by | Architecture Decision → Application<br>Architecture Decision → Technology<br>Architecture Decision → Business Capability<br>Architecture Decision → Initiative / Project |
| `selects` | selects | selected by | Architecture Decision → Technology |
| `supersedes` | supersedes | superseded by | Architecture Decision → Architecture Decision |

## Relationship selection behavior

In the browser relationship form, valid relationship choices are grouped alphabetically by forward relationship label and then alphabetically by target object type. Selecting a rule filters the target selector to that rule's target type.

Only non-archived target records are offered. Draft, Active, and Inactive records are eligible. Target records are sorted alphabetically by name. Changing the relationship rule clears any previously selected target before the valid target list is reloaded.

The same behavior is used when creating and editing relationships. The server independently validates every submitted source/type/target combination against this governed vocabulary before saving.

## Relationship-specific properties

Most relationship types use the common relationship metadata only. `integrates_with` also defines governed properties:

- Integration type
- Protocol
- Direction
- Criticality
- Description
- Data exchanged

## Common relationship metadata

- Description
- Criticality
- Confidence
- Valid From / Valid Until
- Source
- Created / Updated timestamps
- Archived state