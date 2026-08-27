# API Tokens and Service Accounts

OpenEA Community supports Personal Access Tokens (PATs) and independent non-interactive service accounts.

## Personal Access Tokens

A normal signed-in user manages PATs at:

```text
/account/tokens
```

A PAT inherits the user's application roles and also has explicit API scopes.

Token secrets are generated using cryptographically secure randomness, displayed once, and stored only as SHA-256 hashes. OpenEA retains token metadata such as prefix, scopes, expiration, revocation state, and last-used time.

Expiration choices include 30, 60, 90, 180, 365 days, or Never.

## Service accounts

Platform Administrators manage service accounts under:

```text
/admin/service-accounts
```

A service account:

- Has independently assigned OpenEA application roles
- Is non-interactive
- Cannot use password/browser login
- Can receive scoped API tokens

This is appropriate for integrations and automation that should not run under a human user's identity.

## Scopes

Available scopes include:

- `objects:read`
- `objects:write`
- `relationships:read`
- `relationships:write`
- `search:read`
- `impact:read`
- `findings:read`
- `findings:write`
- `reviews:read`
- `reviews:write`
- `analytics:read`

## Authorization model

A Bearer request must satisfy both role and scope:

```text
Identity role permission
        ∩
Token scope
        =
Effective API authority
```

If a token leaks, revoke it immediately. Plaintext token secrets cannot be recovered from the database.
