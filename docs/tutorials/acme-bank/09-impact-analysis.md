# 10. Run Impact Analysis

Impact Analysis traverses the active relationship graph around an architecture object. It answers a different question from risk:

- **Risk:** How concerning is this object or condition?
- **Impact:** What other architecture can be reached from this object through governed relationships?

For the complete behavior, see [Impact Analysis](../../user-guide/impact-analysis.md).

## Goal

You will analyze:

1. **Java 8** to see the architecture affected by an obsolete technology.
2. **Digital Banking** to explore cross-domain business, data, technology, governance, and initiative context.

## 1. Analyze Java 8

1. Select **Explore**.
2. Open **Java 8**.
3. Select **Analyze Impact**.

The default traversal depth in OpenEA Community 1.5.2 is 3, and supported depth is 1 through 5.

The page summarizes:

- Direct impact — depth 1
- Indirect impact — depth 2 or greater
- Traversal depth — configured maximum hops

!!! info "What should be reachable"
    At minimum, the Acme model contains `Legacy Wire Transfer → uses → Java 8` and `Legacy Wire Retirement → retires → Java 8`. Because Impact Analysis traverses active relationships in both stored and inverse directions, starting from Java 8 can reveal the application using it and the initiative retiring it. At deeper traversal depths, OpenEA can continue through those neighbors into additional connected architecture.

!!! note "The graph is derived"
    The Cytoscape graph is a visualization of the traversal result. It is not stored as a separate authoritative diagram.

## 2. Read direction and relationship labels carefully

OpenEA preserves the governed forward or inverse label for each traversed step.

For example, the stored relationship is:

```text
Legacy Wire Transfer → uses → Java 8
```

When you analyze from Java 8, the graph can present the reverse perspective using the relationship's governed inverse label.

This is why you created only one relationship in Chapter 6 rather than creating a duplicate inverse row.

## 3. Change traversal depth

Run Java 8 impact analysis at depth 1.

Compare the result with depth 3.

Depth 1 shows only direct neighbors. Greater depth follows additional connected objects. A larger number is not automatically better: use the lowest depth that answers the architecture question without creating unnecessary visual noise.

## 4. Use filters

Impact Analysis combines filters with clear semantics:

- **Relationship types** control which relationship edges OpenEA is allowed to traverse. Multiple selected relationship types use OR.
- **Result object types** control which destination object types count as results. Multiple selected object types use OR.
- **Traversal depth** limits how many hops OpenEA may follow.
- The three filter groups are combined with AND.

At traversal depths greater than 1, OpenEA preserves intermediate path nodes needed to explain how a matching result was reached.

Try a concrete Digital Banking filter after completing this chapter:

1. Set **Traversal depth** to `1 hop`.
2. Select **supports / supported by** as the only Relationship type.
3. Select **Business Capability** as the only Result object type.
4. Select **Analyze**.

In the canonical Acme Bank model, Digital Banking supports **Customer Management** and **Deposit Account Management**, so both direct Business Capability relationships should appear and unrelated Technologies, Data Objects, Organizations, Roles, Initiatives, Services, and Principles should not appear. If your repository contains only one matching `supports` relationship, only that one result should appear.

Clear the filters to restore the broader architecture context. Filters change only the analysis view; they do not alter the repository.

## 5. Analyze Digital Banking

Open **Digital Banking** and select **Analyze Impact**.

The canonical Acme Bank model connects Digital Banking to multiple domains:

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
├── updates → Customer
└── conforms to → Prefer Strategic Technologies

Digital Banking Modernization → changes → Digital Banking
Standardize Digital Channels on Java 21 → affects → Digital Banking
Retail Banking → owns → Digital Banking
Head of Retail Banking → accountable for → Digital Banking
```

At depth 1, many of these objects should be directly reachable.

At deeper levels, the graph can expose additional context through those neighbors. For example:

```text
Digital Banking
   ↓ supports
Customer Management
   ↑ improves
Digital Banking Modernization
```

or:

```text
Digital Banking
   ↓ uses
Java 21
   ↑ selects
Standardize Digital Channels on Java 21
```

The exact graph layout is generated dynamically, but the paths should be explainable from repository relationships you created.

## 6. Ask architecture questions, not graph questions

Use the graph to answer practical questions such as:

- Which business capabilities could be affected by a Digital Banking change?
- Which technologies are directly used by Digital Banking?
- Which initiative is currently changing it?
- Which decision explains the Java 21 direction?
- Which data objects does it read or update?
- Which organization and role are accountable for it?

The graph is useful when it helps you reason about architecture. A dense graph is not itself an objective.

## 7. Open a node from the graph

Select one of the graph nodes, such as **Java 21** or **Customer Management**.

OpenEA can navigate from a graph node back to the corresponding repository record. Use that behavior to move from a high-level impact view to the authoritative object details.

## 8. Compare impact with the persisted Impact Severity metric

Return to **Digital Banking** and select **View Metrics**.

OpenEA persists an `impact_severity` metric calculated from a depth-3 traversal. The metric and interactive Impact Analysis are related but not identical UI experiences:

- Interactive Impact Analysis lets you choose traversal depth and filters.
- The persisted metric gives a deterministic score and explanation suitable for analytics.

See [Analytics and Repository Health](../../user-guide/analytics.md) for metric behavior.

## Checkpoint

You have now used the same repository relationships in two ways:

```text
Repository graph
   ├──► interactive Impact Analysis
   └──► persisted impact/risk calculations
```

No separate manually maintained diagram was required.

Continue to [Use Portfolios and Roadmaps](10-portfolios-and-roadmaps.md).
