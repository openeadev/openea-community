# Explore the Live Demo

This walkthrough introduces OpenEA Community using the hosted **Northstar Financial** demo repository. No installation is required.

Allow approximately 15–20 minutes.

## 1. Open the demo

Go to:

**[https://demo.openea.dev](https://demo.openea.dev)**

Public credentials are listed at:

**[https://openea.dev/try/](https://openea.dev/try/)**

!!! note "Cold start"
    The demo runs on free hosted infrastructure. If it has been inactive, the first request can take a short time while the service starts.

## 2. Review the dashboard

After signing in, start on the Dashboard. Treat the page as a summary of repository-derived information rather than as a separate reporting database.

The Northstar repository contains applications, technologies, capabilities, data, initiatives, principles, decisions, relationships, calculated metrics, and deliberately seeded architecture issues.

## 3. Explore the repository

Select **Explore** from the left navigation.

Try searching for:

```text
Customer Portal
```

Open the `Customer Portal` Application record.

Northstar seeds this application as a Mission Critical active application. It has relationships to business and technology objects so it is a useful starting point for evaluation.

## 4. Examine architecture context

Open the **Relationships** tab on Customer Portal.

In the baseline demo, Customer Portal includes relationships such as:

```text
Customer Portal ── supports ──► Customer Management
Customer Portal ── uses ──────► Amazon EKS
Customer Portal ── uses ──────► PostgreSQL 17
```

Two active initiatives also change Customer Portal:

- Digital Experience Modernization
- Customer Portal Accessibility Upgrade

This is intentionally useful demo data: it lets the findings engine identify a potential initiative collision.

## 5. Run Impact Analysis

From the object detail page, open **Impact Analysis**.

Start with the default depth. OpenEA traverses active relationships in both directions and keeps the path used to reach each impacted object. You can increase depth up to five and filter by relationship type or resulting object type.

The graph is a visualization of the traversal result. The repository relationships remain authoritative.

## 6. Look at an architecture risk example

Search for:

```text
Python 2.7
```

The demo seeds Python 2.7 as a Technology with lifecycle `End of Support`, strategic status `Retire`, and a vendor support end date in the past.

It is used by:

- Regulatory Reporting
- Legacy Customer Lookup

This lets you see how a technology condition can become application exposure through repository relationships.

## 7. Review Findings

Open **Findings**.

The demo is intentionally imperfect. Examples seeded into Northstar include conditions that can produce findings such as:

- Technology past end of support
- Application uses retiring technology
- Capability with a single application dependency
- Potential duplicate Application Service names
- Data Object with no system of record
- Conflicting systems of record
- Overdue architecture review
- Initiative change collision

Resolved findings are hidden by default in the 1.5.2 baseline. Use the status filter when you want to include resolved history.

## 8. Review Repository Health

Open **Analytics**.

Repository Health summarizes five dimensions:

- Completeness
- Freshness
- Ownership
- Relationship coverage
- Governance

Select a dimension card to see the active objects that are reducing that score and the reason each object is contributing to the gap.

## 9. Explore portfolio views

Open **Portfolio** and review:

- Application Portfolio
- Technology Portfolio
- Capability Map
- Roadmaps

The Application Portfolio derives a TIME-style positioning from business and technical fit. This is a portfolio aid, not an automatic disposition decision.

## 10. Create a temporary architecture record

The public demo account has the Architect role, so you can create and modify repository records.

Create an Application named:

```text
Evaluation Customer App
```

Give it a short description and save it. Then add a `supports` relationship to an existing Business Capability.

This demonstrates the basic OpenEA pattern:

```text
Object
   +
Governed relationship
   +
Metadata
   ↓
Architecture context
```

## 11. Observe background calculations

Repository changes queue background work. The hosted demo runs the OpenEA worker in the same Render container as the web process, so persisted metrics and findings are recalculated shortly after relevant changes.

The normal Docker Compose deployment runs the web and worker as separate containers.

## 12. Archive your test object

Open the record you created and archive it. OpenEA favors archival over destructive deletion for architecture records.

## Next steps

- [Install OpenEA Community](installation.md)
- [Map an Application to a Capability](../tutorials/application-capability.md)
- [Model an Application Technology Stack](../tutorials/application-technology-stack.md)
- [Analyze Application Retirement Impact](../tutorials/retirement-impact.md)
