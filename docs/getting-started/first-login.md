# First Login and Setup

After a clean OpenEA Community installation, complete the following setup steps before loading production architecture data.

## 1. Create the Platform Administrator

If no user exists yet, OpenEA exposes `/setup` for initial account creation.

The first account receives the **Platform Administrator** role.

## 2. Understand Platform Administrator scope

OpenEA separates platform administration from architecture stewardship.

A Platform Administrator can manage users, service accounts, and API tokens. The role does **not** automatically grant create/edit/archive permission for architecture objects.

If your administrator also needs to maintain repository content, assign one of these roles as appropriate:

- **Architecture Administrator**
- **Architect**

## 3. Create normal user accounts

Platform Administrators manage users under **Management → Users**.

For each user, configure:

- Username
- Display name
- Password
- Active state
- One or more application roles

A Platform Administrator cannot deactivate their own account or remove their own Platform Administrator role through the user-management form.

## 4. Choose repository roles

A simple initial assignment model is:

| User type | Suggested role |
| --- | --- |
| EA platform owner | Platform Administrator + Architecture Administrator |
| Enterprise / Solution Architect | Architect |
| Architecture steward who updates existing records | Contributor |
| Read-only stakeholder | Viewer |

See [Users and Permissions](../administration/users-permissions.md) for the full permission model.

## 5. Verify the worker

Analytics and findings are persisted and recalculated asynchronously. In Docker Compose, confirm the worker is healthy and running:

```bash
docker compose ps
```

You should see `postgres`, `web`, and `worker` services.

As a Platform Administrator, also open **Management → Background Processing** and verify the default schedules: Analytics & Metrics every 6 hours and Findings Evaluation every 1 hour. Repository changes still queue event-driven work immediately; the schedules ensure date-dependent conditions are refreshed even while the repository is idle.

If you are troubleshooting calculated data, you can force synchronous processing:

```bash
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

## 6. Decide whether to load sample data

For evaluation or training, load Northstar Financial:

```bash
docker compose exec web python -m app.cli seed-demo
docker compose exec web python -m app.cli recalculate-metrics-now
docker compose exec web python -m app.cli evaluate-findings-now
```

For a production repository, skip the demo and begin with your own architecture records or CSV imports.

## 7. Start with a small architecture slice

Do not try to model the entire enterprise on day one. A useful first slice is:

1. A few Business Capabilities
2. The Applications that support them
3. The Technologies those Applications use
4. The owning Organizations or Roles
5. Relevant Initiatives

That is enough to begin using search, relationship navigation, impact analysis, findings, and portfolio views while the repository grows iteratively.
