# LearnSphere operations runbook

## Routine release

1. Review migration files and database backup status.
2. Run `python manage.py check --deploy` with production environment values.
3. Run `python manage.py migrate --plan` and inspect the plan.
4. Apply migrations and collect static files.
5. Restart the web process.
6. Check `/accounts/health/` and exercise critical role-based paths.
7. Review application and database logs for errors.

## Administrator password reset

List platform administrators without printing passwords:

```bash
python manage.py shell -c "from accounts.models import User; print(list(User.objects.filter(is_superuser=True).values_list('username','email','is_active')))"
```

Reset the password with the internal username:

```bash
python manage.py changepassword ADMIN_USERNAME
```

Login uses the administrator's email address.

## Common diagnostics

```bash
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py check --deploy
python manage.py test --noinput
```

If an email or phone uniqueness error appears, inspect duplicate values before
changing records. Contact details are database-constrained and should not be
made unique by silently replacing another user's account.

## Security boundaries

- Do not run production with `DEBUG=True`.
- Do not expose the PostgreSQL port publicly.
- Keep `.env`, database dumps, credentials CSV files, and provider tokens out
  of source control.
- Use a durable media provider or volume; container filesystems are commonly
  ephemeral.
- Treat `check --deploy` warnings as release blockers unless the warning is
  intentionally documented and covered by infrastructure.
