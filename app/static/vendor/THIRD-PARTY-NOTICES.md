# Third-party browser assets

OpenEA Community 1.5.2 downloads pinned copies of the following browser-side dependencies during the Docker image build and serves them locally at runtime.

| Component | Version | License | Upstream |
| --- | --- | --- | --- |
| Tabler Core | 1.4.0 | MIT | https://github.com/tabler/tabler |
| HTMX | 2.0.10 | BSD-2-Clause | https://github.com/bigskysoftware/htmx |
| Lucide | 1.33.0 | ISC | https://github.com/lucide-icons/lucide |
| Cytoscape.js | 3.33.1 | MIT | https://github.com/cytoscape/cytoscape.js |
| Swagger UI Dist | 5.32.14 | Apache-2.0 | https://github.com/swagger-api/swagger-ui |
| ReDoc | 2.5.0 | MIT | https://github.com/Redocly/redoc |

The asset downloader uses exact package versions rather than floating `latest` URLs. OpenEA does not contact these upstream services from the user's browser during normal operation.

The applicable upstream license and copyright terms continue to govern the downloaded third-party files. This notice does not change OpenEA Community's AGPLv3 license.
