from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "app" / "static" / "vendor"


@dataclass(frozen=True)
class Asset:
    name: str
    version: str
    url: str
    relative_path: str


ASSETS = (
    Asset(
        "Tabler Core CSS",
        "1.4.0",
        "https://cdn.jsdelivr.net/npm/@tabler/core@1.4.0/dist/css/tabler.min.css",
        "tabler/tabler.min.css",
    ),
    Asset(
        "Tabler Core JavaScript",
        "1.4.0",
        "https://cdn.jsdelivr.net/npm/@tabler/core@1.4.0/dist/js/tabler.min.js",
        "tabler/tabler.min.js",
    ),
    Asset(
        "HTMX",
        "2.0.10",
        "https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js",
        "htmx/htmx.min.js",
    ),
    Asset(
        "Lucide",
        "1.33.0",
        "https://cdn.jsdelivr.net/npm/lucide@1.33.0/dist/umd/lucide.min.js",
        "lucide/lucide.min.js",
    ),
    Asset(
        "Cytoscape.js",
        "3.33.1",
        "https://cdn.jsdelivr.net/npm/cytoscape@3.33.1/dist/cytoscape.min.js",
        "cytoscape/cytoscape.min.js",
    ),
    Asset(
        "Swagger UI",
        "5.32.14",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.32.14/swagger-ui-bundle.js",
        "swagger-ui/swagger-ui-bundle.js",
    ),
    Asset(
        "Swagger UI CSS",
        "5.32.14",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.32.14/swagger-ui.css",
        "swagger-ui/swagger-ui.css",
    ),
    Asset(
        "ReDoc",
        "2.5.0",
        "https://cdn.jsdelivr.net/npm/redoc@2.5.0/bundles/redoc.standalone.js",
        "redoc/redoc.standalone.js",
    ),
)


def _download(asset: Asset, output: Path) -> None:
    destination = output / asset.relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = urllib.request.Request(
        asset.url,
        headers={"User-Agent": "OpenEA-Community-frontend-vendor/1.5.2"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} downloading {asset.url}")
        with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent) as handle:
            shutil.copyfileobj(response, handle)
            temporary = Path(handle.name)

    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded an empty file from {asset.url}")
    temporary.replace(destination)
    # NamedTemporaryFile is created with mode 0600. Docker builds run this
    # script as root, but the application serves static files as the unprivileged
    # 'openea' user. Make vendored browser assets world-readable so Starlette can
    # serve them after the container drops privileges.
    destination.chmod(0o644)


def _missing(output: Path) -> list[Asset]:
    missing: list[Asset] = []
    for asset in ASSETS:
        path = output / asset.relative_path
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(asset)
            continue
        try:
            with path.open("rb") as handle:
                handle.read(1)
        except OSError:
            missing.append(asset)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the pinned browser assets OpenEA serves locally at runtime."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Vendor directory (default: app/static/vendor)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that every required asset is present without using the network.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download all pinned assets even when files already exist.",
    )
    args = parser.parse_args()
    output = args.output.resolve()

    if args.check:
        missing = _missing(output)
        if missing:
            print("Missing OpenEA frontend vendor assets:", file=sys.stderr)
            for asset in missing:
                print(f"  - {asset.relative_path} ({asset.name} {asset.version})", file=sys.stderr)
            return 1
        print(f"All {len(ASSETS)} OpenEA frontend vendor assets are present.")
        return 0

    output.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for asset in ASSETS:
        destination = output / asset.relative_path
        if destination.is_file() and not args.force:
            print(f"present  {asset.relative_path}")
            continue
        print(f"fetching {asset.name} {asset.version} -> {asset.relative_path}")
        try:
            _download(asset, output)
        except (OSError, RuntimeError, urllib.error.URLError) as exc:
            failures.append(f"{asset.name} {asset.version}: {exc}")

    if failures:
        print("\nUnable to vendor required frontend assets:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print(
            "\nThe first OpenEA Docker build requires network access to retrieve pinned "
            "frontend assets. For an air-gapped target, build the OpenEA image on a "
            "connected preparation host and transfer it with docker save/docker load.",
            file=sys.stderr,
        )
        return 1

    missing = _missing(output)
    if missing:
        print("Frontend asset vendoring did not complete successfully.", file=sys.stderr)
        return 1
    print(f"Vendored {len(ASSETS)} browser assets for offline runtime use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
