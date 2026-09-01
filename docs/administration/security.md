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
- Hashed API token storage
- Non-interactive service-account enforcement
- Correlation Request IDs on HTTP responses
- Safe unexpected-error handling that keeps stack traces and database details in server logs

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
