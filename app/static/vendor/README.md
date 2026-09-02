# OpenEA browser vendor assets

OpenEA Community serves its browser dependencies from `/static/vendor` so the application can operate without Internet access after its image has been built.

The pinned asset list is maintained in `scripts/vendor_frontend_assets.py`. During a normal Docker build, the script downloads those files into this directory inside the image. The generated third-party files are intentionally not required to be committed to the source repository.

To populate the directory for a non-Docker local development environment while Internet access is available:

```bash
python scripts/vendor_frontend_assets.py
```

To verify a previously populated directory without network access:

```bash
python scripts/vendor_frontend_assets.py --check
```

Runtime templates must reference only the local `/static/vendor/...` paths.
