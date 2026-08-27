# Portfolios and Roadmaps

Portfolio and roadmap views are derived from the architecture repository. They do not create a separate portfolio data store.

## Application Portfolio

The Application Portfolio presents fields such as:

- Lifecycle
- Ownership
- Criticality
- Business fit
- Technical fit
- Strategic fit
- Hosting model
- Persisted Application Risk

OpenEA derives a TIME-style classification from business and technical fit:

| Position | General interpretation |
| --- | --- |
| Invest | Stronger business and technical fit |
| Migrate | Stronger business fit, weaker technical fit |
| Tolerate | Weaker business fit, stronger technical fit |
| Eliminate | Weaker business and technical fit |

!!! important
    TIME-style positioning is a portfolio aid. OpenEA does not automatically decide that an application should be eliminated or migrated.

## Technology Portfolio

The Technology Portfolio brings together:

- Lifecycle
- Strategic status
- Vendor support horizon
- Dependent application count
- Technology Risk

This helps connect technology lifecycle concerns to the applications exposed to them.

## Capability Map

The Capability Map is derived from the Business Capability hierarchy. It overlays:

- Maturity
- Strategic importance
- Supporting application count
- Capability Risk

The hierarchy is stored in repository data through the capability parent reference; the map itself is derived.

## Roadmaps

Roadmaps use structured dates already present in the repository, including:

- Application go-live and retirement dates
- Initiative start and target end dates
- Technology support dates
- Universal validity dates

OpenEA does not persist a separate freeform timeline model in 1.5.2.
