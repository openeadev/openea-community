# 7. Model Initiatives and Architecture Change

Architecture describes not only the current state but also **what is changing it**. OpenEA Community models planned or active change with the **Initiative / Project** object type and governed relationships such as `changes`, `introduces`, `retires`, and `improves`.

For the complete object schema, see [Standard Metamodel](../../reference/metamodel.md). For all valid change relationships, see [Relationship Vocabulary](../../reference/relationships.md).

## Goal

In this chapter you will create two initiatives:

- **Digital Banking Modernization** — an active modernization program
- **Legacy Wire Retirement** — an approved retirement project

You will then connect them to the architecture they affect.

At the end of the chapter, the Acme Bank base model will contain **30 objects** and **47 relationships**.

## 1. Create Digital Banking Modernization

Select **Explore → New → Initiative / Project**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Digital Banking Modernization` |
| Description | `Program to modernize Acme Bank digital channels and supporting technology.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Retail Banking` |
| Initiative Type | `Program` |
| Sponsor | `Head of Retail Banking` |
| Owning Organization | `Retail Banking` |
| Architecture Owner | `Enterprise Architect` |
| Status | `In Progress` |
| Start Date | `2026-01-15` |
| Target End Date | `2027-06-30` |
| Strategic Priority | `High` |
| Delivery Health | `Green` |
| Architecture Engagement Status | `Design` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Leave **Actual End Date** blank because the program is not complete.

Select **Create object**.

!!! info "Why both Record status and Initiative Status exist"
    `Record status` is universal repository metadata. The Initiative-specific `Status` field describes delivery state. In this tutorial, `Record status: Active` and `Initiative status: In Progress` mean the repository record is active and the change program itself is currently in progress.

## 2. Create Legacy Wire Retirement

Select **Explore → New → Initiative / Project**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Legacy Wire Retirement` |
| Description | `Initiative to retire the Legacy Wire Transfer application and remove Java 8.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Payments Technology` |
| Initiative Type | `Project` |
| Sponsor | `Payments Technology` |
| Owning Organization | `Payments Technology` |
| Architecture Owner | `Enterprise Architect` |
| Status | `Approved` |
| Start Date | `2026-10-01` |
| Target End Date | `2027-06-30` |
| Strategic Priority | `High` |
| Delivery Health | `Green` |
| Architecture Engagement Status | `Assessment` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Select **Create object**.

## 3. Connect Digital Banking Modernization to the architecture

Open **Digital Banking Modernization → Relationships → + Add relationship**.

Create:

| Source | Relationship | Target |
| --- | --- | --- |
| Digital Banking Modernization | `changes` | Digital Banking |
| Digital Banking Modernization | `introduces` | Kubernetes |
| Digital Banking Modernization | `improves` | Customer Management |

For each relationship in this tutorial:

- **Confidence:** `High`
- **Source:** `Manual`
- Leave the other relationship metadata blank unless you want to add explanatory text.

These relationships answer three different architecture questions:

- **changes** — which existing architecture is being modified?
- **introduces** — what new architecture is the initiative bringing in?
- **improves** — which business capability is expected to benefit?

## 4. Connect Legacy Wire Retirement

Open **Legacy Wire Retirement → Relationships** and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Legacy Wire Retirement | `retires` | Legacy Wire Transfer |
| Legacy Wire Retirement | `retires` | Java 8 |

This connects the remediation plan to both the problematic application and its obsolete technology.

## 5. Inspect change from the target side

Open **Legacy Wire Transfer → Relationships**.

You should be able to see that the application is being retired by the Legacy Wire Retirement initiative even though the stored relationship was created from the initiative.

Then open **Java 8** and confirm the same change context is visible.

This is an important repository pattern: OpenEA lets a user begin with the architecture object they care about and discover the initiative changing it.

## 6. Review roadmap-relevant dates

You entered structured dates on both initiatives:

```text
Digital Banking Modernization
Start:      2026-01-15
Target End: 2027-06-30

Legacy Wire Retirement
Start:      2026-10-01
Target End: 2027-06-30
```

OpenEA's Roadmaps view later derives timeline entries from these fields. You are not creating a separate roadmap object or manually drawing a timeline.

## 7. Optional architecture-change collision experiment

OpenEA has a built-in rule, `INIT-COLLISION-001`, for architecture objects being changed by multiple active initiatives.

Do **not** add a collision to the canonical Acme model yet. If you want to experiment later, create a second active initiative and connect it with `changes → Digital Banking`. Evaluate findings, observe the collision finding, then archive or remove the test relationship before continuing.

This keeps the core tutorial results predictable while showing how the rule can be exercised.

## Checkpoint

You should now have:

```text
Digital Banking Modernization
├── changes → Digital Banking
├── introduces → Kubernetes
└── improves → Customer Management

Legacy Wire Retirement
├── retires → Legacy Wire Transfer
└── retires → Java 8
```

The repository now represents both current architecture and planned change.

Continue to [Add Governance, Reviews, Principles, and Decisions](07-governance.md).
