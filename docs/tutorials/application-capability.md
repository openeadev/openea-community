# Tutorial: Map an Application to a Business Capability

This tutorial uses the Northstar Financial demo to show the most important OpenEA modeling pattern: connecting an application to the business capability it supports.

## Goal

Create this architecture context:

```text
Evaluation Customer App ── supports ──► Customer Management
```

## Prerequisites

You need the **Architect** or **Architecture Administrator** role to create the Application. A Contributor can create relationships between existing objects but cannot create the new Application itself.

You can use the public demo at [demo.openea.dev](https://demo.openea.dev).

## 1. Review the target capability

Open **Explore** and search for:

```text
Customer Management
```

Open the Business Capability record and review its existing relationships. In Northstar, Customer Management is a high-strategic-importance capability and already has application support.

## 2. Create the application

From **Explore**, select **New → Application**.

Use:

| Field | Suggested value |
| --- | --- |
| Name | Evaluation Customer App |
| Description | Tutorial application used to demonstrate business capability mapping. |
| Record Status | Active |
| Lifecycle | Active |
| Criticality | Medium |
| Business Fit | Good |
| Technical Fit | Good |
| Strategic Fit | Good |
| Source | Manual |
| Confidence | High |

Save the record.

## 3. Create the relationship

Open the new application's **Relationships** tab and add a relationship.

Choose:

```text
Relationship: supports
Target type: Business Capability
Target: Customer Management
```

Save.

## 4. Verify both directions

From the Application, you should see:

```text
Evaluation Customer App supports Customer Management
```

Now open Customer Management. From the capability side, OpenEA can display the governed inverse label:

```text
Customer Management supported by Evaluation Customer App
```

Only one relationship is stored.

## 5. Observe downstream effects

This single relationship can affect:

- Capability supporting-application counts
- Capability Risk components
- Relationship coverage / repository health
- Capability-map overlays
- Impact Analysis paths
- Findings such as missing application support

This is why OpenEA treats relationships as first-class architecture data rather than as decorative lines on a diagram.

## 6. Clean up

If you are using the public demo, archive the tutorial Application when finished. Archiving the object preserves the historical record without leaving it active in the shared evaluation repository.
