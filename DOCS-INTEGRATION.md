# OpenEA Community 1.5.2 Documentation Integration

This documentation set was written against the supplied OpenEA Community 1.5.2 source baseline, including its current metamodel, routes, permissions, analytics, findings, API, CLI, Docker Compose deployment, and Render demo startup model.

## Install into the repository

From the OpenEA Community repository root:

1. Back up or remove the existing legacy `docs/` directory.
2. Copy this package's `docs/` directory into the repository root.
3. Copy `mkdocs.yml` and `requirements-docs.txt` into the repository root.
4. Install the documentation toolchain:

```bash
python -m pip install -r requirements-docs.txt
```

5. Preview locally:

```bash
mkdocs serve
```

6. Open:

```text
http://127.0.0.1:8000
```

7. Before publishing, build strictly:

```bash
mkdocs build --strict
```

## docs.openea.dev

The Markdown source remains in the repository's `docs/` directory, but the generated static site can be published at the root of `https://docs.openea.dev/`.

This is separate from the OpenEA application's `/docs` route, which remains FastAPI Swagger UI.

## Screenshots

The documentation structure reserves `docs/assets/screenshots/` for real OpenEA Community screenshots. The initial documentation does not depend on screenshots so it remains accurate while the screenshot library is built.
