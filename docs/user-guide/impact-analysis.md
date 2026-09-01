# Impact Analysis

Impact Analysis shows how far an architecture object reaches through active repository relationships. It is separate from risk: impact describes connected reach, while risk describes how concerning an object or condition is.

## Start an analysis

Open an architecture object and select **Impact Analysis**.

OpenEA Community 1.5.2 supports traversal depth from 1 through 5. The default is 3.

## How traversal works

OpenEA starts at the selected object and traverses non-archived relationships in both stored and inverse directions.
Archived objects are excluded from normal Impact Analysis, so the graph represents the current architecture. Historical relationships remain preserved in the repository but do not participate when one of their endpoints is archived.

For every result, it preserves:

- Result depth
- Object path
- Relationship path
- Direction used for each step
- Governed forward or inverse label

Cycles are avoided by preventing the same object from appearing twice in a single path.

## Direct and indirect impact

Depth 1 results are direct impacts. Deeper results are indirect impacts.

Example:

```text
Python 2.7
   ▲ used by
   │
Regulatory Reporting
   │ supports
   ▼
Regulatory Reporting capability
```

Depending on the selected root and traversal direction, OpenEA can expose both technology and business reach from the same repository graph.

## Filter semantics

The three controls have different purposes:

- **Relationship types** — determine which relationship edges OpenEA is allowed to traverse.
- **Result object types** — determine which destination object types count as results.
- **Traversal depth** — determines the maximum number of hops from the analyzed root.

Multiple selections **within** Relationship types use OR. Multiple selections **within** Result object types also use OR. The filter groups are then combined with AND.

For example:

```text
(supports OR uses)
AND
(Business Capability OR Technology)
AND
within 2 hops
```

means OpenEA may traverse only `supports` or `uses` edges, counts only Business Capability or Technology destinations as results, and never goes beyond two relationships from the root.

Leave a multi-select filter empty to mean "all" for that filter.

## Explanatory paths at deeper depths

Result object filtering does not remove intermediate objects required to explain how OpenEA reached a matching result.

For example, if the repository contains:

```text
Technology
   ↑ used by
Application
   ↓ supports
Business Capability
```

and you analyze the Technology at depth 2 while filtering results to Business Capability, the Application remains in the graph as the explanatory intermediate node even though it is not itself a matching result.

At depth 1 there are no intermediate path nodes, so a filtered graph should contain only the root, matching destination objects, and matching traversed edges.

## Example: Digital Banking

In the canonical Acme Bank tutorial, Digital Banking has two direct `supports` relationships:

```text
Digital Banking → supports → Customer Management
Digital Banking → supports → Deposit Account Management
```

With:

```text
Traversal depth:     1 hop
Relationship type:   supports / supported by
Result object type:  Business Capability
```

the graph should show the Digital Banking root and those two Business Capability results. Technologies, Data Objects, Organizations, Roles, Initiatives, Application Services, and Principles should not appear.

If your repository contains only one matching direct `supports` relationship, only that one result appears.

## Graph visualization

The Cytoscape.js graph is generated from the filtered impact result. Selecting a node can navigate to the corresponding repository object.

The graph is not stored as authoritative architecture data.

## Impact Severity

OpenEA also persists an `impact_severity` metric using an unfiltered depth-3 traversal. The score is deterministic and uses components for direct dependents, critical dependents, business reach, dependency depth, and strategic importance.

See [Analytics and Repository Health](analytics.md) and [Metric Calculation Reference](../reference/analytics-metrics.md).
