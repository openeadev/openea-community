# OpenEA Community Documentation

**OpenEA Community** is a self-hosted, open-source Enterprise Architecture knowledge and decision-support platform. It connects business capabilities, processes, applications, technologies, data, initiatives, ownership, principles, and architecture decisions in a governed repository.

OpenEA is built around a repository-first principle:

> Architecture objects and governed relationships are the authoritative model. Search, visualizations, impact analysis, analytics, findings, portfolios, and roadmaps are derived from that model.

## Start here

Choose the path that matches what you want to do.

### Evaluate the populated demo

1. Read [What is OpenEA Community?](getting-started/what-is-openea.md).
2. Follow the [Live Demo walkthrough](getting-started/live-demo.md) using the Northstar Financial sample repository.

### Learn OpenEA from an empty repository

1. [Install OpenEA with Docker Compose](getting-started/installation.md) without running `seed-demo`.
2. Complete [First Login and Setup](getting-started/first-login.md).
3. Follow **[Acme Bank: Build an Enterprise Architecture Repository from Scratch](tutorials/acme-bank/index.md)**.

The Acme Bank sequence is the most complete hands-on learning path. It starts with no architecture data, builds all twelve standard object types, connects them with governed relationships, introduces deliberate architecture issues, and then uses findings, analytics, impact analysis, portfolios, roadmaps, CSV imports, governance, reviews, and archival to manage the repository.

## What OpenEA helps you answer

A useful architecture repository should answer questions such as:

- What business capabilities does this application support?
- Which applications support this capability?
- What technologies does this application use?
- Which applications depend on a technology approaching end of support?
- What could be affected if an application or technology is retired?
- Which capabilities depend on only one application?
- Which architecture records have weak ownership, stale reviews, or incomplete relationships?
- Which initiatives are changing the same architecture?
- Which application portfolios warrant investment, migration, tolerance, or elimination review?
- Why was a particular architecture or technology decision made?

## OpenEA Community 1.5.2 at a glance

The 1.5.2 Community baseline includes:

- Twelve standard Enterprise Architecture object types
- Governed relationship types and valid source/target rules
- Schema-validated object-specific metadata
- Local authentication and five application roles
- Repository create, edit, browse, search, and archival workflows
- Governance transitions, reviews, comments, and immutable audit history
- Architecture Decision Records and decision supersession
- Recursive impact analysis with relationship-path explanations
- Deterministic Application, Technology, Capability, Data Quality, and Impact Severity metrics
- Repository Health drill-downs
- Built-in and custom declarative finding rules
- Application and Technology portfolios
- Capability maps and derived roadmaps
- CSV object and relationship imports
- Object CSV export
- REST API v1
- Personal Access Tokens and service accounts
- PostgreSQL-backed background job processing
- Docker Compose deployment

## Live demo

A hosted OpenEA Community demo is available at:

**[https://demo.openea.dev](https://demo.openea.dev)**

Public credentials are available at:

**[https://openea.dev/try/](https://openea.dev/try/)**

The demo contains the fictional **Northstar Financial** architecture repository. It is intentionally populated with useful examples and some architecture issues so that analytics, findings, impact analysis, and portfolio views have meaningful data to display.

!!! note "Shared demonstration environment"
    Demo users can create, edit, and archive architecture records. The hosted repository may be reset when a new Community build is deployed.

## Open source

OpenEA Community is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

- Project website: [openea.dev](https://openea.dev)
- Community source: [github.com/openeadev/openea-community](https://github.com/openeadev/openea-community)
