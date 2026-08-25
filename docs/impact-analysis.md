# Impact Analysis

OpenEA Community 0.8.0 introduces repository-derived impact analysis. Impact is deliberately separate from risk: impact describes architecture reach, not how concerning an object is.

## Traversal model

Impact analysis starts from one active architecture object and traverses active relationship records in either direction. A relationship is still stored only once. When traversal follows the stored direction, OpenEA Community uses the relationship's normal label; when traversal follows the reverse direction, OpenEA Community uses the governed inverse label.

For example, if the repository stores:

`Application -> uses -> Technology`

then analyzing the Technology can traverse to the Application as:

`Technology -> used by -> Application`

and can continue through the Application to other architecture context.

OpenEA Community uses a recursive SQL CTE against PostgreSQL for the traversal. Paths track visited object IDs and refuse to revisit an object already present in the current path, preventing cycles from causing infinite recursion.

## Depth

The default interactive depth is 3 hops. The maximum interactive depth is 5 hops. Requests outside the 1-5 range are rejected server-side.

A direct impact is exactly one relationship away from the analyzed object. An indirect impact is two or more relationships away.

## Explainability

Each result retains one shortest path from the analyzed object to the impacted object. The UI exposes this under **Why is this impacted?**, showing every object and relationship label in the path.

If multiple paths reach the same object at the same shortest depth, OpenEA Community currently presents one of those paths. Path ranking beyond shortest-depth selection is not part of Phase 8.

## Filtering

Relationship-type filters constrain traversal itself. Object-type filters constrain displayed results while retaining intermediate path objects needed to explain why a matching result is impacted.

This distinction prevents a result filter from destroying the relationship path needed for explanation.

## Visualization

The graph is generated from the same impact result and explanatory paths. It is not an authoritative diagram and does not persist layout information. Selecting a node opens the corresponding repository object.

The visualization uses Cytoscape.js as a focused client-side graph library; OpenEA Community remains server-rendered and does not introduce a SPA or Node.js build chain.

## Authorization

Impact analysis is read-only. Any authenticated user, including Viewer, may run it. Normal repository visibility and authentication controls continue to apply.
