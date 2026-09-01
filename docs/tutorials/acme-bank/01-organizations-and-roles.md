# 2. Create Acme Bank Organizations and Roles

Start the architecture repository with ownership context. Many later records can reference an Owner organization or Owner role, so creating these objects first makes the later forms more useful.

For general object-management behavior, use [Manage Architecture Objects](../../user-guide/objects.md). For exact fields supported by Organization and Role, use the [Standard Metamodel](../../reference/metamodel.md).

## What you will create

```text
Acme Bank
├── Retail Banking
├── Payments Technology
└── Enterprise Architecture

Retail Banking
└── Head of Retail Banking

Payments Technology
└── Payments Application Owner

Enterprise Architecture
└── Enterprise Architect
```

You will create four **Organization** objects and three repository **Role** objects.

## 1. Learn the object-creation pattern once

For each object in this tutorial, the basic navigation is:

1. Select **Explore**.
2. Select **New**.
3. Choose the object type.
4. Complete the fields shown in the chapter table.
5. Select **Create object**.

The form is schema-driven, so the type-specific section changes based on the object type you selected.

## 2. Create the Acme Bank enterprise organization

Select **Explore → New → Organization**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Acme Bank` |
| Description | `Fictitious banking enterprise used by the OpenEA Community hands-on tutorial.` |
| Record status | `Active` |
| Criticality | Leave `Not set` |
| Owner organization | `Not set` |
| Owner role | `Not set` |
| Organization Type | `Enterprise` |
| Parent Organization | `Not set` |
| Organization Code | `ACME` |
| External Organization | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Select **Create object**.

### Verify

The detail page should show:

```text
Organization
Acme Bank
```

The **Repository** section should show `Acme Bank` as a tag, `Manual` as Source, and `High` as Confidence.

## 3. Create Retail Banking

Create another **Organization**:

| Field | Value |
| --- | --- |
| Name | `Retail Banking` |
| Description | `Business unit responsible for consumer banking products and customer relationships.` |
| Record status | `Active` |
| Organization Type | `Business Unit` |
| Parent Organization | `Acme Bank` |
| Organization Code | `RB` |
| External Organization | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

The Parent Organization selector works because Acme Bank already exists.

## 4. Create Payments Technology

Create an **Organization**:

| Field | Value |
| --- | --- |
| Name | `Payments Technology` |
| Description | `Technology department responsible for payment applications and services.` |
| Record status | `Active` |
| Organization Type | `Department` |
| Parent Organization | `Acme Bank` |
| Organization Code | `PAYTECH` |
| External Organization | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 5. Create Enterprise Architecture

Create an **Organization**:

| Field | Value |
| --- | --- |
| Name | `Enterprise Architecture` |
| Description | `Enterprise architecture team responsible for architecture governance and standards.` |
| Record status | `Active` |
| Organization Type | `Team` |
| Parent Organization | `Acme Bank` |
| Organization Code | `EA` |
| External Organization | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 6. Create the Head of Retail Banking role

!!! info "Owner organization and Role organization are different concepts"
    **Owner organization** in Core information identifies who stewards the OpenEA repository record. **Role organization** in Role details identifies where the business or architecture role belongs or operates. They may be the same or different. In this tutorial, Acme Bank uses the same organization for both because the organization containing each role also stewards its record. See [Manage Architecture Objects](../../user-guide/objects.md#owner-organization-and-type-specific-organization-fields) for the full explanation.

Select **Explore → New → Role**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Head of Retail Banking` |
| Description | `Business accountability role for Acme Bank retail banking capabilities and products.` |
| Record status | `Active` |
| Owner organization | `Retail Banking` |
| Role Type | `Business Owner` |
| Role organization | `Retail Banking` |
| Responsibilities | `Accountable for retail banking products, customer outcomes, and business capability priorities.` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Select **Create object**.

## 7. Create the Payments Application Owner role

Create a **Role**:

| Field | Value |
| --- | --- |
| Name | `Payments Application Owner` |
| Description | `Application accountability role for Acme Bank payment platforms.` |
| Record status | `Active` |
| Owner organization | `Payments Technology` |
| Role Type | `Application Owner` |
| Role organization | `Payments Technology` |
| Responsibilities | `Accountable for payment application lifecycle, service quality, and technology risk.` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 8. Create the Enterprise Architect role

Create a **Role**:

| Field | Value |
| --- | --- |
| Name | `Enterprise Architect` |
| Description | `Architecture role responsible for cross-domain architecture governance.` |
| Record status | `Active` |
| Owner organization | `Enterprise Architecture` |
| Role Type | `Architecture` |
| Role organization | `Enterprise Architecture` |
| Responsibilities | `Maintains architecture standards, reviews changes, and supports architecture decisions.` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 9. Use Explore to verify your repository

Select **Explore** and set **Object type** to `Organization`.

You should have:

- Acme Bank
- Enterprise Architecture
- Payments Technology
- Retail Banking

Then filter to `Role` and verify:

- Enterprise Architect
- Head of Retail Banking
- Payments Application Owner

You can also search globally for `Acme Bank` to see that the tag and record content are searchable context.

## Why this order matters

OpenEA's object form can reference existing Organization and Role records as structured ownership. Creating ownership context first lets later Application, Business Capability, Technology, Data Object, Initiative, Principle, and Decision records use repository-backed owners instead of relying only on free-text owner fields.

The repository still permits type-specific free-text owner properties such as Application `Business Owner` or `Technical Owner`. The structured **Owner organization** and **Owner role** fields are the cross-cutting ownership fields used by repository-health and finding logic.

## Checkpoint

You should now have **7 objects**:

| Type | Count |
| --- | ---: |
| Organization | 4 |
| Role | 3 |

Continue to [Model the Business Architecture](02-business-architecture.md).
