# Documentation Development

OpenEA Community documentation is maintained in the same repository as the application so product changes and documentation changes can be reviewed together.

Published documentation is available at:

**https://docs.openea.dev/**

## Source layout

```text
docs/                    Markdown source
mkdocs.yml               navigation and site configuration
requirements-docs.txt    documentation-only Python dependencies
```

Do not edit generated HTML under `site/`. The `site/` directory is a local build artifact.

## Install MkDocs tooling

From an activated development environment:

```bash
python -m pip install -r requirements-docs.txt
```

## Preview locally

Start MkDocs in the background:

```bash
make docs
```

Default preview URL:

```text
http://127.0.0.1:8000/
```

If the OpenEA application already uses port 8000:

```bash
make docs DOCS_PORT=8001
```

Check status:

```bash
make docs-status
```

Stop the server:

```bash
make docs-stop
```

## Validate before commit

Run:

```bash
make docs-build
```

This executes:

```bash
mkdocs build --strict
```

When adding a new documentation page, also add it to `mkdocs.yml` if it belongs in the published navigation.

## Publishing

Documentation publishing is automated through GitHub Actions.

```text
edit Markdown / mkdocs.yml
      ↓
preview and build locally
      ↓
commit / merge to main
      ↓
GitHub Actions builds MkDocs
      ↓
GitHub Pages deploys
      ↓
https://docs.openea.dev/
```

The generated site is not committed to the application repository.

## Writing conventions

- Treat the current OpenEA Community implementation as the source of truth.
- Keep Community documentation independent from OpenEA Enterprise capabilities.
- Link to reference pages instead of duplicating long definitions in tutorials.
- Use MkDocs admonitions for system behavior, warnings, and explanatory information rather than presenting those explanations as numbered tutorial steps.
- Prefer actual UI labels and exact governed values.
- State when a behavior applies only to the public demo, a Platform Administrator, or a particular application role.
- Update release notes and upgrade guidance when a maintenance change affects behavior or schema.

## Tutorial model

The **Acme Bank** tutorial is the canonical from-scratch learning sequence. The **Northstar Financial** repository is the populated evaluation/demo model. Keep those two purposes distinct.
