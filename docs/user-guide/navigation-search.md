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

The top bar contains a global architecture search field. Submitting a search opens Explore with the query applied.

OpenEA uses PostgreSQL full-text search and `pg_trgm` fuzzy matching in production. No external search engine is required.

## Explore filters

Explore supports filters for:

- Search text
- Object type
- Record status
- Lifecycle
- Criticality
- Governance status
- Owner
- Tag
- Review status

Results can be sorted and paginated. When a text query is supplied, relevance becomes the effective default sort.

## Aliases and tags

Aliases and tags participate in architecture discovery. They are useful when a system is known by several names or when teams use common classification labels across object types.
