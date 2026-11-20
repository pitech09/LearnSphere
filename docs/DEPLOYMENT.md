# LearnSphere deployment guide

This project is a Django high-school management system. Production should use
PostgreSQL and durable media storage. SQLite and local `media/` storage are for
development or small demonstrations only.

## Required production configuration

Copy `.env.example` to `.env` only for a local deployment, or configure the
same variables in the hosting provider's secret manager. Never commit `.env`.

At minimum, set:

- `DEBUG=False`
- a randomly generated `SECRET_KEY` of at least 50 characters
- the exact public hostname in `ALLOWED_HOSTS`
- the HTTPS origin in `CSRF_TRUSTED_ORIGINS`
- `FORCE_HTTPS=True`, `SESSION_COOKIE_SECURE=True`, and `CSRF_COOKIE_SECURE=True`
- `USE_SQLITE=False` and all PostgreSQL `DB_*` values
- `DEFAULT_FROM_EMAIL` and `SENDGRID_API_KEY` if account notifications are used

Generate a secret with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## First deployment

Run these commands as a release step, before starting the web process:

```bash
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py test --noinput
```

Start the application with:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --access-logfile - --error-logfile -
```

Create the first platform administrator once, using the production database:

```bash
python manage.py createsuperuser
```

The application login form uses the administrator's unique email address. The
Django `changepassword` command still accepts the internal username:

```bash
python manage.py changepassword ADMIN_USERNAME
```

## Docker Compose smoke environment

The included Compose file starts PostgreSQL and the Django application:

```bash
docker compose up --build
```

Open `http://localhost:8000`. The Compose database and password are local-only
defaults and must not be used for production.

## Media and backups

Course videos, uploaded files, profile pictures, payment proofs, and generated
documents must be stored on durable storage. For horizontally scaled hosting,
enable Cloudinary with `CLOUDINARY_MEDIA_ENABLED=True`; otherwise configure a
provider volume mounted at `MEDIA_ROOT`.

Back up the PostgreSQL database before every migration and keep media backups
separate from database backups. Test restoration periodically. A successful
backup command is not proof of a successful restore.

## Health and release checks

The application health endpoint is `/accounts/health/`. Verify it after every
deployment, then verify login, administrator dashboard access, student access,
teacher mark entry, parent portal access, file upload, and report generation.

CI runs Django checks, deployment checks, migration drift checks, static-file
collection, and the automated test suite. External SendGrid, TextBee,
Cloudinary, database, DNS, and browser flows still require live-environment
verification.

## Rollback

Keep the previous application image or release available. If a release fails,
restore the application image first, then restore the database only when the
migration is not backward-compatible. Do not run destructive migration rollback
commands without a verified database backup and a tested recovery plan.
