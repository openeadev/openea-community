# UI branding

OpenEA Community 1.2.0 uses Tabler Core 1.4.0 as the visual foundation while retaining server-rendered Jinja2 templates, HTMX, and focused JavaScript.

## Placeholder assets

Replace these files with final project artwork while keeping their paths stable:

- `app/static/img/openea-mark.svg` — square/icon mark and favicon.
- `app/static/img/openea-wordmark.svg` — horizontal wordmark used in public and authenticated navigation.

SVG is recommended so the assets remain sharp in the sidebar and on high-DPI screens.

## Theme behavior

Light/dark choice is stored only in browser local storage under `openea-theme`. It is not written to the OpenEA user record.

## Colors

The primary OpenEA accent remains blue (`#206bc4`) with white/light surfaces. Dark mode delegates core component values to Tabler and adds a small OpenEA override layer in `app/static/css/app.css`.

## External UI assets

Tabler Core, HTMX, and Lucide are loaded through jsDelivr. No Node.js build process is required. The application's CSP explicitly permits scripts/styles from jsDelivr.
