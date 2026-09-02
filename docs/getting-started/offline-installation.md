# Offline and Air-Gapped Installation

OpenEA Community can run without Internet access after the required container images have been built and staged. The supported runtime does not depend on public CDNs, Google Fonts, external JavaScript, or other browser-hosted Internet resources.

There are two supported installation patterns:

1. **Temporarily connected installation** — allow Internet access for the first image build and image pulls, then disconnect the host.
2. **Fully air-gapped installation** — build and collect the required images on a connected preparation host, transfer them to the isolated host, and start OpenEA with `--no-build`.

## What requires Internet access during a normal first build

A new Docker host normally needs network access for several separate downloads:

| Build/install action | Why network access may be required |
| --- | --- |
| Obtain the OpenEA source | Git clone or release download, unless the source is transferred another way |
| Pull `python:3.10-slim` | Base image used to build the OpenEA application image |
| Pull `postgres:16-alpine` | PostgreSQL runtime image |
| `pip install` during the OpenEA image build | Python packages are resolved/downloaded from PyPI unless already cached/mirrored |
| Frontend asset vendoring during the OpenEA image build | Pinned Tabler, HTMX, Lucide, Cytoscape.js, Swagger UI, and ReDoc files are downloaded and copied into the OpenEA image |

Docker Engine and the Docker Compose plugin must already be installed on the target host. Installing Docker or operating-system packages is outside the OpenEA installation procedure and may itself require Internet access or separately staged packages.

Once the OpenEA application image and PostgreSQL image are present, normal OpenEA operation does not require Internet access.

## Temporarily connected installation

If the OpenEA host can be connected during installation, use the normal procedure:

```bash
docker compose up -d --build
```

Wait for the build and initial image pulls to finish, then verify the application before disconnecting the host:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

You can also verify that the OpenEA browser assets were copied into the built image:

```bash
docker compose exec web python scripts/vendor_frontend_assets.py --check
```

After those steps complete successfully, Internet access can be removed. Refreshing the browser, signing in, using Impact Analysis, switching themes, and opening `/docs` or `/redoc` should continue to work because their browser assets are served locally by OpenEA.

!!! note "Rebuilds can require connectivity again"
    A later `docker compose build` can require network access again if Docker/Python caches are unavailable. If the machine must remain isolated permanently, use the air-gapped image-transfer process below for upgrades as well.

## Fully air-gapped installation

Use a connected preparation host to build the exact OpenEA image that will run on the isolated machine.

### Preparation-host requirements

The preparation host should use a Docker-compatible platform matching the isolated target, especially the same CPU architecture (for example, `amd64` to `amd64`).

Start with the same OpenEA Community 1.5.2 source that will be transferred to the target.

### 1. Build the OpenEA image while connected

From the repository root:

```bash
cp .env.example .env

docker compose build web
```

The Compose configuration tags the resulting application image as:

```text
openea-community:1.5.2
```

unless `OPENEA_IMAGE` is overridden in `.env`.

The build downloads Python dependencies and the pinned browser assets and stores them inside the OpenEA image.

### 2. Pull the PostgreSQL image

```bash
docker pull postgres:16-alpine
```

Verify both required images exist:

```bash
docker image inspect openea-community:1.5.2 >/dev/null
docker image inspect postgres:16-alpine >/dev/null
```

### 3. Export the images

```bash
docker save \
  openea-community:1.5.2 \
  postgres:16-alpine \
  -o openea-community-1.5.2-images.tar
```

Generate a checksum:

```bash
sha256sum openea-community-1.5.2-images.tar \
  > openea-community-1.5.2-images.tar.sha256
```

Transfer these items through your approved offline-media process:

- the OpenEA Community 1.5.2 repository/release directory
- `openea-community-1.5.2-images.tar`
- `openea-community-1.5.2-images.tar.sha256`

### 4. Verify the transfer on the isolated host

```bash
sha256sum -c openea-community-1.5.2-images.tar.sha256
```

### 5. Load the images

```bash
docker load -i openea-community-1.5.2-images.tar
```

Verify:

```bash
docker image inspect openea-community:1.5.2 >/dev/null
docker image inspect postgres:16-alpine >/dev/null
```

### 6. Configure OpenEA

From the transferred repository directory:

```bash
cp .env.example .env
```

Set at least a strong `SECRET_KEY` and `POSTGRES_PASSWORD`. Keep:

```dotenv
OPENEA_IMAGE=openea-community:1.5.2
```

unless you intentionally used a different image tag on the preparation host.

### 7. Start without building

```bash
docker compose up -d --no-build
```

`--no-build` is important on an air-gapped host. It tells Compose to use the transferred OpenEA image instead of trying to rebuild it.

### 8. Verify the isolated deployment

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose exec web alembic current
docker compose exec web python scripts/vendor_frontend_assets.py --check
```

For Community 1.5.2, the expected migration head is:

```text
0016_phase15 (head)
```

Then open:

```text
http://localhost:8000/setup
```

The first-run setup page should retain the full OpenEA styling even when the host has no Internet route.

## What OpenEA does not contact at runtime

The browser UI does not need to contact jsDelivr or another CDN for:

- Tabler CSS/JavaScript
- HTMX
- Lucide icons
- Cytoscape.js
- Swagger UI
- ReDoc

ReDoc is configured not to load Google Fonts, and Swagger UI's external specification validator is disabled. OpenEA's Content Security Policy restricts normal application pages to locally served scripts/styles and locally served/data images.

OpenEA can still communicate with external systems if an administrator intentionally builds an integration around the REST API or places OpenEA behind external infrastructure. Those are deployment choices rather than baseline runtime requirements.

## Preparing future upgrades for an air-gapped host

For each future OpenEA release:

1. Build the new OpenEA image on a connected preparation host.
2. Pull any changed PostgreSQL image required by that release.
3. Export the required images with `docker save`.
4. Transfer and checksum-verify the images and release files.
5. Back up the existing PostgreSQL data.
6. Load the new images on the isolated host.
7. Follow that release's upgrade notes.
8. Start with `docker compose up -d --no-build`.

Do not rebuild on the isolated host unless all required base images, Python packages, and frontend assets have been separately staged for that build process.
