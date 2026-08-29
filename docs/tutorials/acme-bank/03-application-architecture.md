# 4. Model Applications and Application Services

Now add Acme Bank's application architecture.

OpenEA distinguishes an **Application** from an **Application Service**:

- An Application is a deployable or acquired software application relevant to enterprise architecture.
- An Application Service is a logical function exposed or provided by an application.

For the full schema, see the [Standard Metamodel](../../reference/metamodel.md).

## 1. Create Digital Banking

Select **Explore → New → Application**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Digital Banking` |
| Description | `Customer-facing web and mobile banking application.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Application Type | `Custom` |
| Business Owner | `Head of Retail Banking` |
| Technical Owner | `Digital Channels Engineering` |
| Business Fit | `Good` |
| Technical Fit | `Good` |
| Strategic Fit | `Excellent` |
| Hosting Model | `Public Cloud` |
| Delivery Model | `Internal` |
| Go Live Date | `2024-06-01` |
| Rto Hours | `2` |
| Rpo Hours | `0.5` |
| Data Classification | `Restricted` |
| Internet Facing | Check it |
| Aliases | `Online Banking` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Leave Vendor, Product Name, Version, and retirement fields blank because this tutorial treats Digital Banking as an internally developed application.

Select **Create object**.

## 2. Create Core Banking

Create an **Application**:

| Field | Value |
| --- | --- |
| Name | `Core Banking` |
| Description | `Core deposit account processing and account-of-record application.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Application Type | `Commercial` |
| Business Owner | `Head of Retail Banking` |
| Technical Owner | `Core Banking Engineering` |
| Business Fit | `Good` |
| Technical Fit | `Fair` |
| Strategic Fit | `Good` |
| Hosting Model | `Data Center` |
| Delivery Model | `Vendor Product` |
| Vendor | `Example Core Systems` |
| Product Name | `CoreBank Suite` |
| Version | `12` |
| Go Live Date | `2018-03-15` |
| Planned Retirement Date | `2029-12-31` |
| Rto Hours | `1` |
| Rpo Hours | `0.25` |
| Data Classification | `Restricted` |
| Internet Facing | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 3. Create Payments Hub

Create an **Application**:

| Field | Value |
| --- | --- |
| Name | `Payments Hub` |
| Description | `Central application for payment orchestration and payment processing.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |
| Application Type | `Custom` |
| Business Owner | `Payments Operations` |
| Technical Owner | `Payments Technology` |
| Business Fit | `Good` |
| Technical Fit | `Good` |
| Strategic Fit | `Good` |
| Hosting Model | `Private Cloud` |
| Delivery Model | `Internal` |
| Go Live Date | `2023-09-01` |
| Rto Hours | `1` |
| Rpo Hours | `0.25` |
| Data Classification | `Restricted` |
| Internet Facing | Leave unchecked |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 4. Create Legacy Wire Transfer — keep the deliberate gaps

Create an **Application** using the values below.

| Field | Value |
| --- | --- |
| Name | `Legacy Wire Transfer` |
| Description | `Legacy wire-transfer application intentionally modeled with gaps for the findings tutorial.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | **Leave `Not set`** |
| Owner role | **Leave `Not set`** |
| Application Type | `Custom` |
| Business Owner | `Payments Operations` |
| Technical Owner | `Legacy Payments Team` |
| Business Fit | `Good` |
| Technical Fit | **Leave `Not set`** |
| Strategic Fit | `Poor` |
| Hosting Model | `Data Center` |
| Delivery Model | `Internal` |
| Go Live Date | `2012-01-15` |
| Planned Retirement Date | `2027-06-30` |
| Rto Hours | `2` |
| Rpo Hours | `1` |
| Data Classification | `Restricted` |
| Internet Facing | Leave unchecked |
| Tags | `Acme Bank, Tutorial Finding` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Do not fill in the missing structured owner or Technical Fit yet. Those gaps are intentional.

!!! warning "Do not add a capability relationship yet"
    In the relationship chapter you will intentionally leave Legacy Wire Transfer without a `supports → Business Capability` relationship. OpenEA's built-in `APP-CAP-001` rule is designed to detect that condition.

## 5. Create Digital Account Service

Select **Explore → New → Application Service**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Digital Account Service` |
| Description | `Logical service exposing customer account functions to digital channels.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Active` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Service Type | `API` |
| Service Owner | `Digital Channels Engineering` |
| Availability Requirement | `99.9%` |
| Consumer Type | `Digital channels` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 6. Create Payment Processing Service

Create an **Application Service**:

| Field | Value |
| --- | --- |
| Name | `Payment Processing Service` |
| Description | `Logical service for validating and processing customer payments.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Lifecycle stage | `Active` |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |
| Service Type | `API` |
| Service Owner | `Payments Technology` |
| Availability Requirement | `99.99%` |
| Consumer Type | `Internal applications` |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 7. Verify with Explore

Filter **Explore** to `Application`. You should see four records.

Then filter to `Application Service`. You should see two records.

Open **Digital Banking** and review the Overview tab. Notice that the common repository metadata and the Application-specific details are shown separately. This is the pattern OpenEA uses across all standard object types.

## Checkpoint

You should now have **20 objects** total, including:

- 4 Applications
- 2 Application Services

Continue to [Model Data and Technology](04-data-and-technology.md).
