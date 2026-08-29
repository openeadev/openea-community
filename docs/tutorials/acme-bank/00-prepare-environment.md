# 1. Prepare a Clean OpenEA Environment

This chapter establishes the clean starting point for the Acme Bank tutorial and separates platform administration from day-to-day architecture work.

## Goal

At the end of this chapter:

- OpenEA Community 1.5.2 is running.
- The standard OpenEA metamodel is available.
- Northstar Financial has **not** been seeded.
- You have an initial Platform Administrator.
- You have a separate user with the **Architect** application role.
- The web, PostgreSQL, and worker services are running.

For complete installation instructions, see [Install with Docker Compose](../../getting-started/installation.md). For the full role model, see [Users and Permissions](../../administration/users-permissions.md).

## 1. Verify a clean Docker Compose installation

From the OpenEA Community repository directory, start the normal stack if it is not already running:

```bash
docker compose up -d --build
```

The 1.5.2 Docker Compose web command performs two important startup operations automatically:

```text
alembic upgrade head
python -m app.cli seed-system
```

`seed-system` creates the standard OpenEA metamodel and reference definitions. It is **not** the Northstar Financial demo seed.

Check the containers:

```bash
docker compose ps
```

You should have the normal services:

```text
postgres
web
worker
```

The worker matters because repository writes queue recalculation work for persisted analytics and findings.

## 2. Verify the application and database

Check the health endpoints:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

Check the migration head:

```bash
docker compose exec web alembic current
```

For the 1.5.2 baseline, the expected migration head is:

```text
0015_phase15
```

## 3. Do not seed Northstar Financial

For this tutorial, do **not** run:

```bash
docker compose exec web python -m app.cli seed-demo
```

If you have already seeded Northstar in the environment you want to use for training, use a clean database instead of mixing the Acme Bank tutorial with the demo data. The CLI `remove-demo` operation archives demo records rather than making the repository identical to a brand-new database, so a fresh training environment is simpler.

## 4. Create the initial Platform Administrator

Open:

```text
http://localhost:8000/setup
```

If no OpenEA user exists, the **First-run setup** page displays **Create the administrator**.

Use values such as:

| Field | Value |
| --- | --- |
| Username | `admin` |
| Display name | `Acme Platform Administrator` |
| Password | Choose a strong password of at least 12 characters |
| Confirm password | Repeat the same password |

Select **Create administrator**.

The first account receives the **Platform Administrator** application role.

!!! important "Platform Administrator is not an automatic repository editor"
    In OpenEA Community 1.5.2, Platform Administrator is intentionally separate from architecture stewardship. That role manages users, service accounts, and API tokens, but it does not automatically grant create/edit/archive permission for architecture objects. See [Users and Permissions](../../administration/users-permissions.md).

## 5. Create the Acme architect user

After signing in as the Platform Administrator:

1. In the left navigation, find **Management**.
2. Select **Users**.
3. Select **Add user**.
4. Enter:

| Field | Value |
| --- | --- |
| Username | `acme.architect` |
| Display name | `Acme Enterprise Architect` |
| Password | Choose a password of at least 12 characters |
| Application roles | Check **Architect** only |

5. Select **Create user**.

OpenEA allows a user to have multiple application roles, but this tutorial intentionally uses a simple separation:

```text
admin
└── Platform Administrator

acme.architect
└── Architect
```

That makes it clear which tasks require platform administration and which tasks are normal architecture work.

## 6. Sign in as the Architect

Sign out from the sidebar and sign in again as:

```text
Username: acme.architect
```

Use the password you assigned.

As an Architect, the sidebar should include the primary architecture workspaces and **Management → Import**, but it should not expose the Platform Administrator-only user-management functions.

## 7. Verify that Explore is empty

Select **Explore**.

A new installation with no demo data should contain no architecture objects yet. The standard **object types**, enumerations, relationship rules, and finding rules exist because they are system/reference data; the architecture repository itself is what you are about to build.

## 8. Understand the tutorial's role terminology

OpenEA has two different concepts named “role”:

- **Application roles** control what a signed-in OpenEA user can do: Platform Administrator, Architecture Administrator, Architect, Contributor, Viewer.
- The repository object type **Role** represents a business or architecture responsibility such as “Head of Retail Banking.”

They are intentionally different. In the next chapter you will create repository Role objects; that does not create login accounts or change OpenEA authorization.

## Checkpoint

Before continuing, confirm:

- [ ] You can sign in as `acme.architect`.
- [ ] **Explore** contains no business architecture records.
- [ ] You did not run `seed-demo`.
- [ ] `docker compose ps` shows the worker running.
- [ ] You understand that OpenEA application roles and repository Role objects are separate concepts.

Continue to [Create Acme Bank Organizations and Roles](01-organizations-and-roles.md).
