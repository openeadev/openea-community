# Portfolio, Capability Maps, and Roadmaps

OpenEA Community 0.11.0 adds repository-derived portfolio and roadmap views. These views do not create a second source of architecture truth.

## Application Portfolio

The Application Portfolio displays lifecycle, owner, criticality, business fit, technical fit, strategic fit, hosting model, and persisted Application Risk. A TIME-style classification is derived from business and technical fit:

- **Invest**: stronger business and technical fit.
- **Migrate**: stronger business fit with weaker technical fit.
- **Tolerate**: weaker business fit with stronger technical fit.
- **Eliminate**: weaker business and technical fit.

This classification is a portfolio aid, not an automatic disposition decision.

## Technology Portfolio

The Technology Portfolio shows lifecycle, strategic status, vendor support horizon, dependent application count, and persisted Technology Risk.

## Capability Map

The Capability Map is derived from the Business Capability hierarchy. It overlays maturity, strategic importance, supporting application count, and persisted Capability Risk. The hierarchy remains repository data; the map does not store a separate diagram.

## Roadmaps

Roadmaps are derived from structured dates including application go-live/retirement dates, initiative start/end dates, technology support dates, and universal validity dates. No freeform timeline data is persisted.
