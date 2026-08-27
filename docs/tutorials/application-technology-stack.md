# Tutorial: Model an Application Technology Stack

This tutorial models Technologies used by an Application and shows how technology lifecycle becomes application exposure.

## Northstar example

The demo already contains:

```text
Customer Portal ── uses ──► Amazon EKS
Customer Portal ── uses ──► PostgreSQL 17
```

It also contains a deliberately risky example:

```text
Regulatory Reporting ── uses ──► Python 2.7
```

Python 2.7 is seeded with lifecycle `End of Support` and strategic status `Retire`.

## 1. Open an application

Search for `Customer Portal` and open the Application.

Review fields such as lifecycle, criticality, business fit, technical fit, and hosting model.

## 2. Review existing Technologies

Open the Relationships tab and locate `uses` relationships. Open `Amazon EKS` and `PostgreSQL 17` in separate tabs if useful.

Notice that Technology objects contain lifecycle and strategy information independently from the Application.

## 3. Add another Technology relationship

If you want to practice in the demo, add a valid Technology relationship to a temporary Application you created rather than changing Northstar's core sample.

For an Application, choose:

```text
Relationship: uses
Target: an existing Technology
```

## 4. Compare with the risky example

Search for `Regulatory Reporting` and open its Technology relationship to `Python 2.7`.

Then open **Analytics** or the object's analytics view and review the relationship between:

- Technology lifecycle/support status
- Technology Risk
- Application technology exposure
- Application Risk
- Findings

OpenEA's Application Risk uses the highest persisted risk among directly related Technologies rather than averaging away a single high-risk dependency.

## 5. Architecture lesson

Model Technologies at the architectural product/platform level relevant to decision-making—not every runtime instance.

A good Technology relationship answers:

> "This Application depends on this technology choice in a way that matters to lifecycle, strategy, support, risk, or architecture planning."
