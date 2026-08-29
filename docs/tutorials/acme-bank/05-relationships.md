# 6. Connect the Architecture with Relationships

You now have architecture objects, but most of their value is still isolated inside individual records. This chapter connects the Acme Bank repository using OpenEA's governed relationship vocabulary.

This is the point where the repository becomes an **architecture model** rather than a catalog.

For the complete relationship rules, see [Relationship Vocabulary](../../reference/relationships.md). For the generic create/edit/archive workflow, see [Manage Relationships](../../user-guide/relationships.md).

## Goal

At the end of this chapter, you will have connected Acme Bank's business, application, data, and technology domains while intentionally preserving a few gaps for the findings tutorial.

You will create **42 relationships** in this chapter.

!!! important "Relationship direction matters"
    OpenEA stores the relationship from the source object to the target object. For example, create `Digital Banking → supports → Customer Management` from the **Digital Banking** record. Do not create an inverse row from Customer Management back to Digital Banking. OpenEA displays the governed inverse label automatically when appropriate.

## 1. Learn the relationship workflow with one relationship

Start with **Consumer Banking → requires → Customer Management**.

1. Select **Explore**.
2. Open **Consumer Banking**.
3. Select the **Relationships** tab.
4. Select **+ Add relationship**.
5. In **Relationship type**, choose:

   ```text
   requires → Business Capability
   ```

6. In **Target object**, choose **Customer Management**.
7. Leave **Description**, **Criticality**, **Valid from**, and **Valid until** blank for this tutorial relationship.
8. Set **Confidence** to `High`.
9. Set **Source** to `Manual`.
10. Select **Save relationship**.

Return to the Relationships tab. You should see the new relationship.

Open **Customer Management** and look at its Relationships tab. OpenEA can show the relationship from the inverse perspective even though you created only one row.

## 2. Connect the business product to capabilities

From **Consumer Banking**, create these additional relationships:

| Source | Relationship | Target |
| --- | --- | --- |
| Consumer Banking | `requires` | Deposit Account Management |
| Consumer Banking | `requires` | Payments |

Do **not** connect Consumer Banking to Regulatory Reporting for this tutorial. Regulatory Reporting remains a capability in the repository, but it is not part of the Consumer Banking product model we are building.

After this step, Consumer Banking should require exactly three capabilities:

```text
Consumer Banking
├── requires → Customer Management
├── requires → Deposit Account Management
└── requires → Payments
```

## 3. Connect business processes to capabilities

Create these relationships from the process records:

| Source | Relationship | Target |
| --- | --- | --- |
| Open Customer Account | `realizes` | Customer Management |
| Open Customer Account | `realizes` | Deposit Account Management |
| Process Customer Payment | `realizes` | Payments |

This models the distinction between **what the bank is able to do** (capabilities) and **how work is performed** (processes).

## 4. Add organizational ownership and process performance

Open the organization records and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Retail Banking | `owns` | Consumer Banking |
| Retail Banking | `owns` | Customer Management |
| Retail Banking | `owns` | Digital Banking |
| Retail Banking | `owns` | Core Banking |
| Payments Technology | `owns` | Payments Hub |
| Retail Banking | `performs` | Open Customer Account |
| Payments Technology | `performs` | Process Customer Payment |

Notice that OpenEA supports both structured owner fields on records and governed ownership relationships. They serve related but different purposes:

- **Owner organization / Owner role fields** support repository metadata, quality checks, and portfolio display.
- **Relationships** make ownership and accountability part of the traversable architecture model.

For the exact ownership behavior used by metrics and findings, see [Objects and Metadata](../../concepts/objects.md) and [Analytics and Repository Health](../../user-guide/analytics.md).

## 5. Add role accountability

Open each repository Role and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Head of Retail Banking | `accountable for` | Customer Management |
| Head of Retail Banking | `accountable for` | Digital Banking |
| Payments Application Owner | `accountable for` | Payments Hub |

Do not confuse these repository Role objects with OpenEA authorization roles such as Architect or Contributor. See [Users and Permissions](../../administration/users-permissions.md) for that distinction.

## 6. Connect applications to business capabilities

Create these application relationships:

| Source | Relationship | Target |
| --- | --- | --- |
| Digital Banking | `supports` | Customer Management |
| Digital Banking | `supports` | Deposit Account Management |
| Core Banking | `supports` | Deposit Account Management |
| Payments Hub | `supports` | Payments |

!!! warning "Leave Legacy Wire Transfer unmapped"
    Do **not** add a `supports → Business Capability` relationship from **Legacy Wire Transfer**. This is intentional. The built-in `APP-CAP-001` finding rule should later identify the application as having no capability mapping.

Also leave **Regulatory Reporting** without a supporting Application. That deliberate gap is used by `CAP-APP-001` later.

At this point the capability support model should be:

```text
Customer Management
└── supported by ← Digital Banking

Deposit Account Management
├── supported by ← Digital Banking
└── supported by ← Core Banking

Payments
└── supported by ← Payments Hub

Regulatory Reporting
└── no supporting application yet
```

This configuration also deliberately gives Customer Management and Payments only one supporting application each, which can trigger OpenEA's single-application-dependency signal (`CAP-APP-002`).

## 7. Connect applications to application services

Create:

| Source | Relationship | Target |
| --- | --- | --- |
| Digital Banking | `provides` | Digital Account Service |
| Payments Hub | `provides` | Payment Processing Service |

Then open **Payment Processing Service** and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Payment Processing Service | `supports` | Process Customer Payment |

This gives the model a path from an application, through a logical application service, to a business process.

## 8. Model application technology dependencies

Create the following `uses` relationships.

### Digital Banking

From **Digital Banking**:

| Relationship | Target |
| --- | --- |
| `uses` | Java 21 |
| `uses` | PostgreSQL 17 |
| `uses` | Kubernetes |

### Core Banking

From **Core Banking**:

| Relationship | Target |
| --- | --- |
| `uses` | PostgreSQL 17 |

### Payments Hub

From **Payments Hub**:

| Relationship | Target |
| --- | --- |
| `uses` | Java 21 |
| `uses` | PostgreSQL 17 |
| `uses` | Kubernetes |

### Legacy Wire Transfer

From **Legacy Wire Transfer**:

| Relationship | Target |
| --- | --- |
| `uses` | Java 8 |

This last relationship is intentionally problematic. Java 8 was modeled with:

```text
Lifecycle stage: End of Support
Strategic Status: Retire
Vendor Support End: 2022-03-31
```

Once findings are evaluated, that combination should make the Legacy Wire Transfer risk visible in several ways.

## 9. Connect application services to technology

Create:

| Source | Relationship | Target |
| --- | --- | --- |
| Digital Account Service | `uses` | Java 21 |
| Payment Processing Service | `uses` | Java 21 |

Application Services can use Technology directly in the 1.5.2 metamodel.

## 10. Establish systems of record

Create these relationships:

| Source | Relationship | Target |
| --- | --- | --- |
| Core Banking | `system of record for` | Customer |
| Core Banking | `system of record for` | Account |
| Payments Hub | `system of record for` | Payment |

!!! warning "Leave Regulatory Report unresolved"
    Do **not** create a system-of-record relationship for **Regulatory Report** yet. The built-in `DATA-SOR-001` finding rule should later detect that the Data Object has no system of record.

## 11. Model data access

From **Digital Banking**, create:

| Relationship | Target |
| --- | --- |
| `reads` | Customer |
| `reads` | Account |
| `updates` | Customer |

From **Payments Hub**, create:

| Relationship | Target |
| --- | --- |
| `creates` | Payment |
| `updates` | Payment |
| `reads` | Account |

OpenEA treats `creates`, `reads`, `updates`, and `system of record for` as distinct governed relationships. Use the relationship that accurately communicates the architectural meaning; do not use `uses` as a generic substitute for Data Objects.

## 12. Verify the connected model

Open **Digital Banking → Relationships**. You should now be able to trace several architecture concerns from one application:

```text
Digital Banking
├── supports → Customer Management
├── supports → Deposit Account Management
├── provides → Digital Account Service
├── uses → Java 21
├── uses → PostgreSQL 17
├── uses → Kubernetes
├── reads → Customer
├── reads → Account
└── updates → Customer
```

Open **Core Banking**, **Payments Hub**, and **Legacy Wire Transfer** and perform the same check.

## 13. Relationship count checkpoint

You created 42 relationships in this chapter. You do not need to count database rows manually, but this checklist helps identify missing sections:

| Relationship area | Expected count |
| --- | ---: |
| Product → capability | 3 |
| Process → capability | 3 |
| Organization ownership/process | 7 |
| Role accountability | 3 |
| Application → capability | 4 |
| Application/service structure | 3 |
| Application → technology | 8 |
| Application Service → technology | 2 |
| Systems of record | 3 |
| Data access | 6 |
| **Total** | **42** |

If your model differs, revisit the applicable section before continuing. Later tutorials assume these relationships exist.

## What you learned

You have now used OpenEA's governed graph to connect:

```text
Product
  ↓ requires
Capability
  ↑ supports
Application
  ↓ uses
Technology
```

and:

```text
Organization → owns → Application
Role → accountable for → Application
Application → reads/updates → Data Object
Application → provides → Application Service
```

The repository now contains enough cross-domain context for meaningful impact analysis, risk calculations, and findings.

Continue to [Model Initiatives and Architecture Change](06-initiatives.md).
