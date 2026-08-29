# 5. Model Data and Technology

This chapter adds the information and technology domains needed to explain what Acme Bank applications process and what technology they depend on.

You will create four **Data Objects** and four **Technologies**.

## Data Object guidance

OpenEA's Data Object represents **logical business information**, not a physical database table. For example, `Customer` is appropriate; `CUSTOMER_MASTER_TBL` would normally be too implementation-specific for this object type.

## 1. Create Customer

Select **Explore → New → Data Object**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Customer` |
| Description | `Logical customer master information used across Acme Bank.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Data Domain | `Customer` |
| Data Owner | `Head of Retail Banking` |
| Data Steward Role | `Head of Retail Banking` |
| Classification | `Restricted` |
| Retention Requirement | `7 years after relationship ends` |
| Personally Identifiable | Check it |
| Regulated | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 2. Create Account

Create a **Data Object**:

| Field | Value |
| --- | --- |
| Name | `Account` |
| Description | `Logical deposit-account information including account status and balances.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Owner organization | `Retail Banking` |
| Owner role | `Head of Retail Banking` |
| Data Domain | `Accounts` |
| Data Owner | `Head of Retail Banking` |
| Data Steward Role | `Head of Retail Banking` |
| Classification | `Restricted` |
| Retention Requirement | `7 years after account closure` |
| Personally Identifiable | Check it |
| Regulated | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 3. Create Payment

Create a **Data Object**:

| Field | Value |
| --- | --- |
| Name | `Payment` |
| Description | `Logical payment instruction and payment status information.` |
| Record status | `Active` |
| Criticality | `Mission Critical` |
| Owner organization | `Payments Technology` |
| Owner role | `Payments Application Owner` |
| Data Domain | `Payments` |
| Data Owner | `Payments Operations` |
| Data Steward Role | `Payments Application Owner` |
| Classification | `Restricted` |
| Retention Requirement | `7 years` |
| Personally Identifiable | Check it |
| Regulated | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 4. Create Regulatory Report — deliberately leave it without a system of record

Create a **Data Object**:

| Field | Value |
| --- | --- |
| Name | `Regulatory Report` |
| Description | `Logical regulatory-report information intentionally left without a system of record for the findings tutorial.` |
| Record status | `Active` |
| Criticality | `High` |
| Owner organization | `Retail Banking` |
| Data Domain | `Regulatory` |
| Data Owner | `Regulatory Reporting` |
| Classification | `Confidential` |
| Retention Requirement | `7 years` |
| Personally Identifiable | Leave unchecked |
| Regulated | Check it |
| Tags | `Acme Bank, Tutorial Finding` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Later, do **not** create a `system of record for` relationship to this object before the findings chapter. The built-in `DATA-SOR-001` rule detects Data Objects with no system of record.

---

# Technologies

A Technology in OpenEA represents an architectural technology product or platform, not a particular server or operational instance.

## 5. Create Java 21

Select **Explore → New → Technology**.

Enter:

| Field | Value |
| --- | --- |
| Name | `Java 21` |
| Description | `Strategic Java runtime used for modern Acme Bank applications.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Current` |
| Technology Category | `Runtime` |
| Vendor | `Eclipse Adoptium` |
| Product | `Temurin` |
| Version | `21` |
| Strategic Status | `Strategic` |
| Approved For New Use | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Leave the support-end fields blank for this training record.

## 6. Create PostgreSQL 17

Create a **Technology**:

| Field | Value |
| --- | --- |
| Name | `PostgreSQL 17` |
| Description | `Relational database platform used by Acme Bank applications.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Current` |
| Technology Category | `Database` |
| Vendor | `PostgreSQL Global Development Group` |
| Product | `PostgreSQL` |
| Version | `17` |
| Strategic Status | `Adopt` |
| Approved For New Use | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 7. Create Kubernetes

Create a **Technology**:

| Field | Value |
| --- | --- |
| Name | `Kubernetes` |
| Description | `Container orchestration platform used for modern Acme Bank workloads.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `Current` |
| Technology Category | `Container Platform` |
| Vendor | `Cloud Native Computing Foundation` |
| Product | `Kubernetes` |
| Version | `1.33` |
| Strategic Status | `Strategic` |
| Approved For New Use | Check it |
| Tags | `Acme Bank` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

## 8. Create Java 8 — deliberately model end-of-support risk

Create a **Technology**:

| Field | Value |
| --- | --- |
| Name | `Java 8` |
| Description | `Legacy Java runtime intentionally modeled as end of support for the findings tutorial.` |
| Record status | `Active` |
| Criticality | `High` |
| Lifecycle stage | `End of Support` |
| Technology Category | `Runtime` |
| Vendor | `Oracle` |
| Product | `Java` |
| Version | `8` |
| Strategic Status | `Retire` |
| Vendor Support End | `2022-03-31` |
| Approved For New Use | Leave unchecked |
| Tags | `Acme Bank, Tutorial Finding` |
| Source | `Manual` |
| Confidence | `High` |
| Review frequency | `Annual` |

Do not “correct” the support date. The tutorial wants OpenEA to detect that the support horizon is already past.

## 9. Verify the domain objects

Filter **Explore** by Data Object and then Technology.

You should have:

```text
Data Objects
- Account
- Customer
- Payment
- Regulatory Report

Technologies
- Java 21
- Java 8
- Kubernetes
- PostgreSQL 17
```

At this point, Java 8's status is merely repository data. The risk becomes contextually more important when you connect Legacy Wire Transfer to Java 8 in the next chapter.

## Checkpoint

You now have **28 objects** total.

Continue to [Connect the Architecture with Relationships](05-relationships.md).
