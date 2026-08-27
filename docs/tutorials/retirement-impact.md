# Tutorial: Analyze Application Retirement Impact

Use Impact Analysis before deciding to retire an application or technology.

## Scenario

Northstar contains `Legacy Customer Lookup`, an Application with lifecycle `Tolerated` and a planned retirement date. It uses `Python 2.7`, which is already past end of support in the demo.

The question is not only whether the application should retire. The architecture question is:

> What depends on it, what does it support, and what else must change with it?

## 1. Open the candidate

Search for:

```text
Legacy Customer Lookup
```

Review its lifecycle, criticality, ownership, relationships, and planned retirement date.

## 2. Run Impact Analysis

Open **Impact Analysis** and start at depth 3.

Review:

- Direct results
- Indirect results
- Relationship labels
- Path explanations
- Graph nodes

## 3. Change depth

Compare depth 1 with depth 3.

Depth 1 answers "what is immediately connected?" Deeper traversal can expose secondary architecture reach.

Use depth 5 only when needed; a larger graph is not automatically a better analysis.

## 4. Filter deliberately

Try restricting the view to business or application object types, or restricting traversal to relevant relationship types.

Filtering helps answer a specific question without changing the underlying repository.

## 5. Check related findings and analytics

Review the Application's metrics and Findings. A retirement decision should consider both:

- **Impact** — how far the object reaches
- **Risk** — how concerning its current state is

OpenEA keeps these concepts separate so a highly connected object is not automatically treated as risky, and a risky object is not assumed to have broad impact.

## 6. Record the decision

If this were a real retirement decision, consider creating an Architecture Decision and relating it to the affected Application, Technology, Capability, or Initiative using the governed decision relationships.
