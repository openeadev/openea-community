# 11. Use Portfolios and Roadmaps

OpenEA Community 1.5.2 derives portfolio and roadmap views from the repository you have already built. These views do not become a second source of truth.

For full behavior, see [Portfolios and Roadmaps](../../user-guide/portfolios-roadmaps.md).

## Goal

You will use:

- Application Portfolio
- Technology Portfolio
- Capability Map
- Roadmaps

You will verify that each view reflects Acme Bank repository data.

## 1. Open the Application Portfolio

Select **Portfolio**, then **Application Portfolio**.

You should see the four manually created applications:

- Core Banking
- Digital Banking
- Legacy Wire Transfer
- Payments Hub

The table brings together repository fields and persisted risk, including:

- Lifecycle
- Owner
- Criticality
- Business Fit
- Technical Fit
- Strategic Fit
- TIME-style position
- Risk
- Hosting

If risk shows `Not calculated`, run:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
```

and refresh the page.

## 2. Interpret the TIME-style position

OpenEA derives a portfolio position from Business Fit and Technical Fit.

For the canonical Acme records:

| Application | Business Fit | Technical Fit | Expected TIME-style position |
| --- | --- | --- | --- |
| Digital Banking | Good | Good | Invest |
| Core Banking | Good | Fair | Migrate |
| Payments Hub | Good | Good | Invest |
| Legacy Wire Transfer | Good | Not set → treated as Unknown | Migrate |

OpenEA Community 1.5.2 maps missing Technical Fit to `Unknown` for portfolio positioning. The fit map treats `Unknown` at the same numeric level as `Fair`, so a Good-business-fit / Unknown-technical-fit application falls into `Migrate`.

!!! important
    A TIME-style position is an analytical aid, not an automated architecture decision. The application should still be evaluated using business context, risk, lifecycle, initiatives, and decisions.

## 3. Filter the Application Portfolio

Try the **Lifecycle** filter and choose `Active`.

All four tutorial applications should currently match.

If calculated risk bands are available, try the **Risk** filter and then clear it. Filters affect only the view.

## 4. Open the Technology Portfolio

Return to **Portfolio** and choose **Technology Portfolio**.

You should see:

- Java 21
- Java 8
- Kubernetes
- PostgreSQL 17

The view includes:

- Lifecycle
- Strategic Status
- Support End
- Dependent Apps
- Risk

### Check Java 8

Java 8 should show:

```text
Lifecycle: End of Support
Strategic Status: Retire
Support End: 2022-03-31
```

Its dependent application count should include **Legacy Wire Transfer** because that Application has an active `uses → Java 8` relationship.

### Check PostgreSQL 17

The canonical model has direct Application `uses` relationships from:

- Digital Banking
- Core Banking
- Payments Hub

Therefore, PostgreSQL 17 should have three directly dependent Applications in this portfolio calculation.

Application Service technology use is not counted as an Application dependency in that specific portfolio column because the service calculates direct Application sources of `uses` relationships.

That distinction is an example of why reference documentation matters: the word “dependency” can mean different things in different views, while the implementation uses a precise definition.

## 5. Filter the Technology Portfolio

Try:

```text
Lifecycle = End of Support
```

Java 8 should remain.

Then clear that filter and try:

```text
Strategic status = Strategic
```

Java 21 and Kubernetes should match the canonical tutorial data.

## 6. Open the Capability Map

Return to **Portfolio** and choose **Capability Map**.

The tutorial capabilities are all level-1 capabilities with no parent capability, so they appear as roots rather than as a deep hierarchy:

- Customer Management
- Deposit Account Management
- Payments
- Regulatory Reporting

Try each available overlay:

- Capability Risk
- Application Risk
- Technology Risk
- Maturity
- Strategic Importance
- Supporting Application Count

## 7. Verify the Supporting Application Count overlay

Choose **Supporting Application Count**.

Based on the relationships you created:

| Capability | Supporting Applications |
| --- | ---: |
| Customer Management | 1 |
| Deposit Account Management | 2 |
| Payments | 1 |
| Regulatory Reporting | 0 |

These counts should correspond to the capability findings you inspected earlier.

The map and the findings are different views of the same underlying relationships.

## 8. Compare maturity

Choose the **Maturity** overlay.

The canonical values are:

| Capability | Current maturity | Target maturity |
| --- | --- | --- |
| Customer Management | Defined | Managed |
| Deposit Account Management | Managed | Optimized |
| Payments | Managed | Optimized |
| Regulatory Reporting | Developing | Managed |

The Capability Map displays current maturity. The target maturity remains available on the capability record for planning context.

## 9. Open Roadmaps

Select **Roadmaps** from the main navigation.

OpenEA derives roadmap rows from structured dates already stored on repository objects.

You should see timeline information for objects such as:

### Applications

| Application | Start | End / milestone |
| --- | --- | --- |
| Legacy Wire Transfer | 2012-01-15 | 2027-06-30 |
| Core Banking | 2018-03-15 | 2029-12-31 |
| Payments Hub | 2023-09-01 | — |
| Digital Banking | 2024-06-01 | — |

The Application row uses Go Live Date as the preferred start date and Actual Retirement Date / Planned Retirement Date as the preferred end date.

### Initiatives

| Initiative | Start | End / milestone |
| --- | --- | --- |
| Digital Banking Modernization | 2026-01-15 | 2027-06-30 |
| Legacy Wire Retirement | 2026-10-01 | 2027-06-30 |

### Technology

Java 8 has a vendor support date and therefore contributes a Technology roadmap milestone:

```text
2022-03-31
```

That date is in the past, which is consistent with both its Technology Portfolio view and the `TECH-EOS-001` finding.

## 10. Understand the repository-first connection

You did not enter any data directly into the Portfolio or Roadmaps views.

Instead:

```text
Application fields ───────────┐
Technology lifecycle/dates ──┤
Capability properties ───────┼──► Portfolio / Capability Map / Roadmaps
Relationships ────────────────┤
Persisted metrics ────────────┘
```

That is the repository-first principle in practice.

## Checkpoint

You have now used the Acme Bank repository for navigation, findings, analytics, impact analysis, portfolios, capability mapping, and roadmaps without creating parallel authoritative datasets.

Continue to [Import Additional Architecture Data with CSV](11-csv-imports.md).
