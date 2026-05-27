"""
Django settings for config project.
High School LMS Version (Clean Structure)
"""

import os
from decouple import config
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

import course
import quiz
import result

# -------------------------------------------------
# BASE DIRECTORY
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# -------------------------------------------------
# SECURITY
# -------------------------------------------------
def env_bool(name, default=False):
    value = config(name, default=default)
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"1", "true", "yes", "on", "debug", "dev", "development"}:
        return True
    if value in {"0", "false", "no", "off", "release", "prod", "production", ""}:
        return False
    return default


def env_list(name, default):
    value = config(name, default=default)
    if isinstance(value, (list, tuple)):
        return list(value)
    return [item.strip() for item in str(value).split(",") if item.strip()]


DEBUG = env_bool("DEBUG", default=False)

SECRET_KEY = config(
    "SECRET_KEY",
    default="unsafe-dev-only-secret-key" if DEBUG else "",
)
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is disabled.")

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,learnsphere-app.onrender.com,.onrender.com",
)


# -------------------------------------------------
# USER MODEL (HIGH SCHOOL LMS CORE)
# -------------------------------------------------
AUTH_USER_MODEL = "accounts.User"


# -------------------------------------------------
# APPS
# -------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "django_filters",
]

PROJECT_APPS = [
    "core.apps.CoreConfig",
    "accounts.apps.AccountsConfig",
    "course.apps.CourseConfig",
    "result.apps.ResultConfig",
    "search.apps.SearchConfig",
    "quiz.apps.QuizConfig",
    "payments.apps.PaymentsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS


# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.SchoolSuspensionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.school_trial",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# -------------------------------------------------
# DATABASE
# -------------------------------------------------
"""DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}"""


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------------------------------
# AUTH
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Maseru"

USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
    ("es", _("Spanish")),
)

LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]
TRANSLATABLE_MODEL_MODULES = [quiz, course, result]  # Add your model modules here for localization support

# -------------------------------------------------
# STATIC FILES
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0


# -------------------------------------------------
# MEDIA (IMPORTANT FOR LMS FILES + VIDEOS)
# -------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DATA_UPLOAD_MAX_MEMORY_SIZE = config("DATA_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024, cast=int)
FILE_UPLOAD_MAX_MEMORY_SIZE = config("FILE_UPLOAD_MAX_MEMORY_SIZE", default=5 * 1024 * 1024, cast=int)


# -------------------------------------------------
# LOGIN / LOGOUT FLOW
# -------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# -------------------------------------------------
# CRISPY FORMS
# -------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://learnsphere.onrender.com",
)


# -------------------------------------------------
# SECURITY HARDENING
# -------------------------------------------------
FORCE_HTTPS = env_bool("FORCE_HTTPS", default=False)

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = FORCE_HTTPS
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=FORCE_HTTPS)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

if FORCE_HTTPS:
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=True)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "learnsphere-default-cache",
    }
}



# =============================
# Email config

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
SENDGRID_API_KEY=config("SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL=config("DEFAULT_FROM_EMAIL")

# =============================
# TextBee SMS config
# Leave TEXTBEE_API_KEY or TEXTBEE_DEVICE_ID blank in development to log SMS
# messages instead of calling a live provider.

TEXTBEE_API_KEY = config("TEXTBEE_API_KEY", default="")
TEXTBEE_DEVICE_ID = config("TEXTBEE_DEVICE_ID", default="")
TEXTBEE_BASE_URL = config("TEXTBEE_BASE_URL", default="https://api.textbee.dev")


# -------------------------------------------------
# LOGGING (LMS ACTIVITY DEBUGGING)
# -------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG" if DEBUG else "INFO",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


# -------------------------------------------------
#  HIGH SCHOOL STRUCTURE CONSTANTS
# (MATCHES YOUR CORE MODELS)
# -------------------------------------------------

# Grades / Levels (used by Student + Course)
LEVEL_CHOICES = (
    ("F1", _("Form 1")),
    ("F2", _("Form 2")),
    ("F3", _("Form 3")),
    ("F4", _("Form 4")),
    ("F5", _("Form 5")),

)

LECTURER_ID_PREFIX = "LEC"
STUDENT_ID_PREFIX = "STU"
PARENT_ID_PREFIX = "PAR"

# Session status
SESSION_STATUS = (
    ("current", _("Current Session")),
    ("archived", _("Archived")),
)

# Quarter system (matches Semester model)
SEMESTER_CHOICES = (
    ("Q1", _("Quarter 1")),
    ("Q2", _("Quarter 2")),
    ("Q3", _("Quarter 3")),
    ("Q4", _("Quarter 4")),
)

# Gender (optional student profiles)
GENDER = (
    ("M", _("Male")),
    ("F", _("Female")),
)

# -------------------------------------------------
# OPTIONAL PAYMENTS (FUTURE LMS FEATURE)
# -------------------------------------------------
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
