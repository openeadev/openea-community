# Navigation and Search

The authenticated OpenEA Community shell organizes work into three main areas.

## Workspace

- **Dashboard** — repository summary and current architecture signals
- **Explore** — search, filter, browse, create, and open architecture objects
- **Portfolio** — Application Portfolio, Technology Portfolio, and Capability Map
- **Roadmaps** — derived architecture timelines

## Governance

- **Decisions** — Architecture Decision workspace
- **Reviews** — overdue review workspace
- **Findings** — current architecture findings and evidence
- **Analytics** — Repository Health and persisted risk metrics

## Management

Management options are shown according to role:

- **Import** — Architect and Architecture Administrator
- **Finding Rules** — Architecture Administrator
- **Users** — Platform Administrator
- **Service Accounts** — Platform Administrator
- **API Tokens** — Platform Administrator

Every signed-in user can manage their own Personal Access Tokens from the sidebar footer.

## Global search

The top bar contains a global architecture search field. Submitting a search opens Explore with the query applied. Global search uses the normal repository scope, so archived records are excluded by default. On the Explore results page, change **Record status** to **Archived** or **All records** when historical records are required.

OpenEA uses PostgreSQL full-text search and `pg_trgm` fuzzy matching in production. No external search engine is required.

## Explore filters

Explore supports filters for:

- Search text
- Object type
- Record status / repository scope
- Lifecycle
- Criticality
- Governance status
- Owner
- Tag
- Review status

Results can be sorted and paginated. When a text query is supplied, relevance becomes the effective default sort.

## Aliases and tags

Aliases and tags participate in architecture discovery. They are useful when a system is known by several names or when teams use common classification labels across object types.


## Current and archived records

The **Record status** selector combines normal status filtering with archival discovery:

| Choice | Result |
| --- | --- |
| All current records | Draft, Active, and Inactive records; archived records are excluded. |
| Draft | Current Draft records only. |
| Active | Current Active records only. |
| Inactive | Current Inactive records only. |
| Archived | Archived records only. |
| All records | Current and archived records together. |

Archived rows are visually marked in Explore. Opening one shows the retained historical record and, for authorized users, a **Restore** action.
