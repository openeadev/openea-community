# OpenEA Community 1.5.3

OpenEA Community 1.5.3 is a customer-readiness release focused on making the Community distribution easier to recover, operate, diagnose, move, learn, and support.

The scope was informed by the operational work already planned for OpenEA Community and by external product feedback that consistently recognized the repository-first model and explainable analytics while identifying self-hosting, operational confidence, adoption maturity, and integration readiness as areas prospective users will evaluate.

## Planned deliverables

### 1. Administrator Account Recovery

Provide a supported recovery path when a local Platform Administrator loses access.

Planned capabilities:

- secure interactive password-reset CLI
- Platform Administrator role validation
- lockout-state clearing during password recovery
- audit event for recovery actions
- documented recovery and verification procedure

**Milestone 1 status:** implemented.

### 2. Platform Diagnostics and System Health

Give Platform Administrators a consolidated view of the health of the OpenEA runtime.

Planned capabilities include:

- OpenEA application version
- database connectivity
- schema/migration status
- worker and background-processing status
- current/failed queued-job visibility
- configuration warnings that can be safely shown without exposing secrets
- troubleshooting guidance tied to failed checks

**Status:** planned.

### 3. Backup, Restore, and Upgrade Tooling

Move beyond command examples toward supported operational workflows.

Planned capabilities include:

- repeatable backup helper
- restore helper with explicit destructive-operation confirmation
- pre-upgrade backup guidance
- post-restore and post-upgrade verification
- documented rollback boundaries
- preservation of `.env`/secrets as a separate operator responsibility

**Status:** planned.

### 4. Complete Repository Portability

Strengthen OpenEA's existing CSV and API portability so organizations can extract the governed repository without reconstructing relationships manually.

Initial 1.5.3 target:

- Relationship CSV Export
- deterministic source/target identifiers suitable for re-import
- filters consistent with object export where applicable
- documentation for moving object and relationship data between repositories

**Status:** planned.

### 5. Help and Feedback Workflow

Create an explicit path from product use to Community feedback without adding silent telemetry.

Planned capabilities include:

- Help & Feedback entry in the application
- Report a Bug
- Request a Feature
- Ask a Question / Community support
- safe support-information summary containing version and non-secret deployment diagnostics
- links to the appropriate OpenEA GitHub/community destinations

OpenEA Community will not silently collect architecture data or usage telemetry as part of this work.

**Status:** planned.

### 6. First-Run and Customer Onboarding Improvements

Reduce the amount of Enterprise Architecture and OpenEA-specific knowledge required to move from installation to a useful repository.

Planned capabilities include:

- clearer first-run next steps after initial administrator creation
- guided clean-repository path
- direct links to the live product documentation and Acme Bank tutorial
- clearer distinction between demo data and production repository setup
- contextual guidance for the first objects, relationships, impact analysis, findings, and portfolio views

**Status:** planned.

## Milestone 1 - Administrator Account Recovery

The first implementation slice adds:

```bash
python -m app.cli reset-admin-password --username admin
```

The command:

- accepts only an existing local Platform Administrator
- prompts interactively for the new password and confirmation
- enforces the normal minimum password length
- replaces the Argon2id password hash
- clears failed-login and temporary-lockout state
- records an audited `PasswordReset` event using source `Administration CLI`
- does not reactivate an intentionally disabled account
- does not expose a password command-line argument

No database migration is required for this milestone.
