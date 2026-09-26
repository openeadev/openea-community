# Security

OpenEA Community 1.5.2 includes several application-security controls, but secure operation still depends on deployment configuration.

## Built-in controls

The baseline includes:

- Argon2id password hashing
- Signed HttpOnly browser sessions
- SameSite cookies
- HTTPS-aware Secure cookie behavior
- CSRF protection for browser writes
- Temporary authentication lockout/backoff
- Server-side role authorization
- Schema validation for dynamic object properties
- Relationship-rule validation
- SQLAlchemy parameterized database access
- Immutable PostgreSQL audit events
- Baseline security headers
- Runtime browser assets served locally rather than from public CDNs
- Hashed API token storage
- Non-interactive service-account enforcement
- Correlation Request IDs on HTTP responses
- Safe unexpected-error handling that keeps stack traces and database details in server logs
- Optional Google reCAPTCHA v2 checkbox protection for browser login

## Offline browser-asset policy

OpenEA Community 1.5.2 does not require public browser CDNs during normal operation. Tabler, HTMX, Lucide, Cytoscape.js, Swagger UI, and ReDoc are copied into the OpenEA image during the build and served from `/static/vendor`.

By default, the normal application Content Security Policy allows scripts and styles from the OpenEA origin only. The locally hosted API documentation keeps the small inline-script/style allowances required by Swagger UI/ReDoc, but no CDN origins are allowed. ReDoc is configured without Google Fonts, and Swagger UI's external validator is disabled. If login reCAPTCHA is explicitly enabled, only the `/login` response adds the Google reCAPTCHA script, frame, and connection origins required by that optional control.

This means an installed OpenEA instance can continue to render its full UI after the host is disconnected from the Internet. See [Offline and Air-Gapped Installation](../getting-started/offline-installation.md).

## Production checklist

- Use a long random `SECRET_KEY`.
- Set `BASE_URL` to the public HTTPS URL.
- Terminate traffic through HTTPS.
- Keep `DEBUG=false`.
- Protect PostgreSQL from untrusted networks.
- Use strong database credentials.
- Restrict Platform Administrator assignment.
- Grant only the API scopes integrations require.
- Back up PostgreSQL.
- Keep OpenEA and its Python dependencies updated through tested Community releases.

## Token handling

PAT and service-account token secrets are shown only once. OpenEA stores only a SHA-256 digest and metadata.

If a token is suspected to be exposed, revoke it rather than attempting to recover or reuse its plaintext secret.

## Vulnerability reporting

Do not publish exploitable vulnerability details in a public issue. Use the repository host's private security-reporting mechanism when available.

## Error information and Request IDs

OpenEA assigns a Request ID to each HTTP request and returns it in the `X-Request-ID` response header. If an unexpected browser error occurs, the branded error page displays that Request ID rather than exposing a Python traceback or database exception. Unexpected API `500` responses return a safe message plus `request_id`.

Administrators should use the Request ID to correlate the user's error with server logs. Do not copy raw stack traces, SQL errors, credentials, token values, or database connection strings into user-facing error messages. See [Troubleshooting](troubleshooting.md).

## Optional login reCAPTCHA

OpenEA Community can protect the interactive `/login` form with Google reCAPTCHA v2 using the visible **I'm not a robot** checkbox. The feature is disabled by default and does not affect API-token authentication, service accounts, or the initial `/setup` flow.

Configuration is deliberately split between deployment secrets and an administrative switch:

- `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` are environment variables.
- The enabled/disabled state is stored in PostgreSQL and changed by a Platform Administrator under **Management → Settings**.
- OpenEA does not store the secret key in PostgreSQL or display it in the browser.

When enabled, OpenEA verifies the submitted reCAPTCHA response with Google **before** attempting username/password authentication. A missing, rejected, expired, or duplicate challenge does not consume a password attempt. If Google's verification service cannot be reached, OpenEA fails the login closed rather than bypassing the challenge.

The login page's Content Security Policy remains self-only when reCAPTCHA is disabled. When it is enabled and correctly configured, the `/login` response narrowly permits the Google reCAPTCHA script, frame, and connection origins required by the widget; other OpenEA pages keep the normal local-only policy.

Enabling this feature intentionally introduces a runtime Internet dependency for interactive browser login. Leave it disabled for offline or air-gapped deployments.
