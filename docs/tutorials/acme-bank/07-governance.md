# 8. Add Governance, Reviews, Principles, and Decisions

This chapter adds the two governance object types that complete the standard OpenEA Community metamodel:

- **Architecture Principle**
- **Architecture Decision**

You will also use controlled governance transitions and the review workflow instead of editing governance status directly.

For the general workflow, see [Reviews and Architecture Decisions](../../user-guide/reviews-decisions.md). For governance concepts and history behavior, see [Governance and History](../../concepts/governance.md).

## Goal

At the end of this chapter:

- All **12 standard OpenEA object types** are represented in Acme Bank.
- The base repository contains **32 objects**.
- The Architecture Principle is `Approved`.
- The Architecture Decision is `Accepted`.
- The decision is connected to the principle, Java 21, Digital Banking, and Digital Banking Modernization.
- Regulatory Reporting has an intentionally overdue next review date.
- The base repository contains **53 relationships**.

## 1. Create the Architecture Principle

Select **Explore → New → Architecture Principle**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Prefer Strategic Technologies` |
| Description | `Acme Bank principle requiring new solutions to use technologies identified as Adopt or Strategic.` |
| Record status | `Active` |
| Owner organization | `Enterprise Architecture` |
| Owner role | `Enterprise Architect` |
| Statement | `New solutions should use technologies designated Adopt or Strategic unless an approved exception exists.` |
| Rationale | `Standard technologies reduce operational complexity, supportability risk, and duplicated engineering effort.` |
| Implications | `Architecture reviews should identify non-strategic technologies and document exceptions.` |
| Category | `Technology` |
| Owner | `Enterprise Architecture` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

You may leave **Effective Date** and **Review Date** blank for now.

!!! info "Principle status on creation"
    The form contains the schema-driven **Principle Status** field, but OpenEA Community 1.5.2 forces a newly created Architecture Principle to `Draft`. Later status changes are controlled by the Lifecycle workflow.

Select **Create object**. OpenEA saves the principle and opens the new **Prefer Strategic Technologies** record.

## 2. Approve the principle through the Lifecycle workflow

On the **Prefer Strategic Technologies** record that OpenEA opened after creation, select the **Lifecycle** tab.

The current principle status should be `Draft`.

OpenEA 1.5.2 allows these principle transitions:

```text
Draft → Proposed → Approved → Deprecated → Retired
          │
          └──────→ Draft
```

For this tutorial:

1. From `Draft`, choose `Proposed` and apply the transition.
2. Confirm the record now shows `Proposed`.
3. Choose `Approved` and apply the transition.
4. Confirm the principle status is now `Approved`.

Do not edit the object to change this status; use the Lifecycle transition controls.

## 3. Connect architecture to the principle

Open **Digital Banking → Relationships** and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Digital Banking | `conforms to` | Prefer Strategic Technologies |

Open **Java 21 → Relationships** and create:

| Source | Relationship | Target |
| --- | --- | --- |
| Java 21 | `conforms to` | Prefer Strategic Technologies |

These relationships make conformance an explicit part of the architecture model rather than a comment buried in a record.

## 4. Create the Architecture Decision

Select **Explore → New → Architecture Decision**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Standardize Digital Channels on Java 21` |
| Description | `Architecture decision to standardize modern digital-channel services on Java 21.` |
| Record status | `Active` |
| Owner organization | `Enterprise Architecture` |
| Owner role | `Enterprise Architect` |
| Context | `Acme Bank is modernizing digital banking services and needs a supported strategic application runtime.` |
| Decision | `Use Java 21 as the standard runtime for newly modernized digital-channel services.` |
| Rationale | `Java 21 is current and aligns with the Acme Bank strategic technology direction.` |
| Alternatives Considered | `Continue Java 8; move all services to a different runtime.` |
| Consequences | `Teams must upgrade build pipelines and application dependencies to Java 21.` |
| Decision Date | `2026-08-15` |
| Effective Date | `2026-09-01` |
| Review Date | `2027-09-01` |
| Decision Owner | `Enterprise Architect` |
| Approving Body | `Architecture Review Board` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Leave **Exception Expiration** blank.

!!! info "OpenEA controls the decision number and initial status"
    **Decision Number** is generated automatically. OpenEA assigns a value such as `ADR-0001`; the exact number depends on other Architecture Decisions already in the repository.

    **Decision Status** is also controlled. A new Architecture Decision is forced to `Draft` in OpenEA Community 1.5.2, and later status changes are performed through the Lifecycle workflow.

Select **Create object**. OpenEA saves the decision and opens the new **Standardize Digital Channels on Java 21** record.

## 5. Accept the Architecture Decision

On the **Standardize Digital Channels on Java 21** record that OpenEA opened after creation, select the **Lifecycle** tab.

The standard path used here is:

```text
Draft → Proposed → Accepted
```

Perform these transitions:

1. `Draft` → `Proposed`
2. `Proposed` → `Accepted`

Confirm that the decision now shows `Accepted`.

OpenEA also supports later states including `Superseded` and `Deprecated`, but do not use those states in the base tutorial.

## 6. Connect the decision to the architecture

From **Standardize Digital Channels on Java 21 → Relationships**, create:

| Source | Relationship | Target |
| --- | --- | --- |
| Standardize Digital Channels on Java 21 | `conforms to` | Prefer Strategic Technologies |
| Standardize Digital Channels on Java 21 | `selects` | Java 21 |
| Standardize Digital Channels on Java 21 | `affects` | Digital Banking |
| Standardize Digital Channels on Java 21 | `affects` | Digital Banking Modernization |

This creates an explainable chain:

```text
Architecture Principle
        ▲
        │ conforms to
Architecture Decision
        │
        ├── selects → Java 21
        ├── affects → Digital Banking
        └── affects → Digital Banking Modernization
```

If an architect later asks why Java 21 was selected for the modernization, the repository contains an explicit decision record and relationships rather than relying on institutional memory.

## 7. Create an intentionally overdue review

Now use the normal review workflow on **Regulatory Reporting**.

1. Select **Explore** and open **Regulatory Reporting**.
2. Select the **Lifecycle** tab.
3. In **Review notes**, enter:

   ```text
   Tutorial review intentionally schedules an overdue next date to demonstrate findings.
   ```

4. In **Next review date**, enter:

   ```text
   2026-01-01
   ```

5. Select **Mark reviewed**.

The next-review date is intentionally in the past. Leave it that way until the remediation chapter.

!!! note "Review frequency behavior"
    If you leave Next review date blank when marking a record reviewed, OpenEA can derive the next date from the record's configured review frequency. Here you enter a past date explicitly because the tutorial needs a deterministic overdue-review condition.

## 8. Inspect the Reviews workspace

Select **Reviews** from the Governance section of the navigation.

Regulatory Reporting should appear because its explicit next-review date is in the past. The **Attention reason** column explains why the row needs attention and can also show related review context, such as no completed review, a `Needs Review` governance state, or low/unknown confidence when those conditions apply.

The Reviews workspace preserves the same overdue-review scope; the explanation does not create a second source of architecture records or broaden which records qualify.

## 9. Verify all twelve object types

You have now created at least one of every standard OpenEA Community 1.5.2 object type:

| Domain | Object type | Acme example |
| --- | --- | --- |
| Business | Business Product | Consumer Banking |
| Business | Business Capability | Customer Management |
| Business | Business Process | Open Customer Account |
| Business | Organization | Acme Bank |
| Business | Role | Enterprise Architect |
| Application | Application | Digital Banking |
| Application | Application Service | Digital Account Service |
| Information | Data Object | Customer |
| Technology | Technology | Java 21 |
| Change | Initiative / Project | Digital Banking Modernization |
| Governance | Architecture Principle | Prefer Strategic Technologies |
| Governance | Architecture Decision | Standardize Digital Channels on Java 21 |

The base Acme Bank model is now complete enough to exercise the analysis features.

Continue to [Use Findings and Analytics](08-findings-and-analytics.md).
