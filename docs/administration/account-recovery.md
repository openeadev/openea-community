# Administrator Account Recovery

OpenEA Community 1.5.3 adds a supported terminal workflow for recovering a local Platform Administrator account when the administrator cannot sign in because the password is unknown or the account is temporarily locked after repeated failed attempts.

## Reset a Platform Administrator password

For a Docker Compose installation:

```bash
docker compose exec web python -m app.cli reset-admin-password --username admin
```

For a local Python installation:

```bash
python -m app.cli reset-admin-password --username admin
```

The command verifies that the target is a local **Platform Administrator** before prompting for a new password. Password entry is interactive so the new password is not supplied as a command-line argument or written into shell history.

The new password must meet the normal OpenEA minimum of 12 characters.

## What the command changes

A successful reset:

- replaces the Argon2id password hash
- clears `failed_login_count`
- clears the temporary `locked_until` login lock
- writes a `PasswordReset` audit event with source `Administration CLI`

The command never writes the plaintext password to the database or audit history.

## What the command does not change

The recovery command does not:

- create a new administrator
- add the Platform Administrator role to another user
- reset a service-account token
- reactivate an intentionally disabled user

If the target administrator is inactive, OpenEA changes the password but prints a warning. Another active Platform Administrator must reactivate the account through **Management → Users**.

## Security considerations

Run account recovery only from a trusted host with administrative access to the OpenEA deployment. Shell access to the application container or runtime environment should be protected as privileged administrative access.

Do not add a `--password` argument or otherwise place the password directly on the command line. Interactive entry avoids exposing the password through shell history or process listings.

## Verify recovery

After the command succeeds:

1. Open the normal OpenEA login page.
2. Sign in using the recovered administrator username and new password.
3. Confirm that the administrator can access **Management**.
4. Review the audit history if operational policy requires confirmation of the recovery action.
