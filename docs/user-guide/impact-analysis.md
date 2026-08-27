# Impact Analysis

Impact Analysis shows how far an architecture object reaches through active repository relationships. It is separate from risk: impact describes connected reach, while risk describes how concerning an object or condition is.

## Start an analysis

Open an architecture object and select **Impact Analysis**.

OpenEA Community 1.5.2 supports traversal depth from 1 through 5. The default is 3.

## How traversal works

OpenEA starts at the selected object and traverses active relationships in both stored and inverse directions.

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
   ▲ uses
   │
Regulatory Reporting
   │ supports
   ▼
Regulatory Reporting capability
```

Depending on the selected root and traversal direction, OpenEA can expose both technology and business reach from the same repository graph.

## Filters

Impact Analysis can restrict traversal by relationship type and restrict displayed results by object type. These filters do not alter the repository; they only change the analysis view.

## Graph visualization

The Cytoscape.js graph is generated from the impact result. Selecting a node can navigate to the corresponding repository object.

The graph is not stored as authoritative architecture data.

## Impact Severity

OpenEA also persists an `impact_severity` metric using a depth-3 traversal. The score is deterministic and uses components for direct dependents, critical dependents, business reach, dependency depth, and strategic importance.
