# 3. Model the Business Architecture

Now model what Acme Bank offers, what it must be able to do, and the processes that realize those capabilities.

This chapter creates three additional standard OpenEA object types:

- **Business Product**
- **Business Capability**
- **Business Process**

Do not create relationships yet. Chapter 6 connects the objects after the major domains exist.

## 1. Create the Consumer Banking business product

Select **Explore → New → Business Product**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Consumer Banking` |
| Description | `Banking products and services offered to Acme Bank retail customers.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Active` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Product Type | `Financial Service` |
| Business Owner | `Head of Retail Banking` |
| Customer Segment | `Retail customers` |
| Strategic Importance | `High` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Select **Create object**.

!!! note "Structured owner vs. Business Owner text"
    `Owner organization` and `Owner role` are common repository references. `Business Owner` is a Business Product-specific text field. This tutorial populates both where useful so you can see the distinction. See [Objects and Metadata](../../concepts/objects.md).

## 2. Create Customer Management

Select **Explore → New → Business Capability**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Customer Management` |
| Description | `Ability to establish, understand, and manage customer relationships.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Capability Level | `1` |
| Parent Capability | `Not set` |
| Business Owner | `Head of Retail Banking` |
| Maturity | `Defined` |
| Target Maturity | `Managed` |
| Strategic Importance | `High` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Save the object.

Business Capability does not expose a lifecycle-stage selector in the 1.5.2 standard metamodel. Use Record status and governance/review information for its repository state.

## 3. Create Deposit Account Management

Create a **Business Capability**:

| Field | Value |
| --- | --- |
| Name | `Deposit Account Management` |
| Description | `Ability to open, maintain, and service deposit accounts.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Capability Level | `1` |
| Business Owner | `Head of Retail Banking` |
| Maturity | `Managed` |
| Target Maturity | `Optimized` |
| Strategic Importance | `High` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 4. Create Payments

Create a **Business Capability**:

| Field | Value |
| --- | --- |
| Name | `Payments` |
| Description | `Ability to initiate, process, settle, and track customer payments.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Capability Level | `1` |
| Business Owner | `Head of Retail Banking` |
| Maturity | `Managed` |
| Target Maturity | `Optimized` |
| Strategic Importance | `High` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 5. Create Regulatory Reporting — deliberately incomplete downstream support

Create a **Business Capability**:

| Field | Value |
| --- | --- |
| Name | `Regulatory Reporting` |
| Description | `Ability to produce and submit required regulatory reports.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Retail Banking` |
| Owner role | Leave `Not set` |
| Capability Level | `1` |
| Business Owner | `Head of Retail Banking` |
| Maturity | `Developing` |
| Target Maturity | `Managed` |
| Strategic Importance | `High` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Do not add an Application support relationship to this capability later until the findings chapter. We want OpenEA to detect that it has no supporting application.

## 6. Create Open Customer Account

Select **Explore → New → Business Process**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Open Customer Account` |
| Description | `Process used to onboard a retail customer and establish a deposit account.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Active` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Parent Process | `Not set` |
| Process Owner | `Retail Banking Operations` |
| Frequency | `Daily` |
| Business Criticality | `High` |
| Automation Level | `Hybrid` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 7. Create Process Customer Payment

Create a **Business Process**:

| Field | Value |
| --- | --- |
| Name | `Process Customer Payment` |
| Description | `Process used to validate, route, and record a customer payment.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |
| Parent Process | `Not set` |
| Process Owner | `Payments Operations` |
| Frequency | `Continuous` |
| Business Criticality | `Mission Critical` |
| Automation Level | `Mostly Automated` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 8. Verify the business slice

Use **Explore** and the Object type filter.

You should now have:

| Object type | Objects |
| --- | --- |
| Business Product | Consumer Banking |
| Business Capability | Customer Management; Deposit Account Management; Payments; Regulatory Reporting |
| Business Process | Open Customer Account; Process Customer Payment |

At this stage they are still mostly isolated records. That is intentional. OpenEA becomes much more useful when you connect them in Chapter 6.

## Architecture reasoning

The three object types answer different questions:

```text
Business Product
    What do we offer?

Business Capability
    What must the enterprise be able to do?

Business Process
    How is work performed?
```

Do not use these labels interchangeably. Keeping the concepts distinct makes later relationships and impact analysis more meaningful.

## Checkpoint

Your repository should now contain **14 objects** total:

- 4 Organizations
- 3 Roles
- 1 Business Product
- 4 Business Capabilities
- 2 Business Processes

Continue to [Model Applications and Application Services](03-application-architecture.md).
