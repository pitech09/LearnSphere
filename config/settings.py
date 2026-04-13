"""
Django settings for config project.
High School LMS Version (Clean Structure)
"""

import os
from decouple import config
from django.utils.translation import gettext_lazy as _

# -------------------------------------------------
# BASE DIRECTORY
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = config(
    "SECRET_KEY",
    default="o!ld8nrt4vc*h1zoey*wj48x*q0#ss12h=+zh)kk^6b3aygg=!"
)

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "adilmohak1.pythonanywhere.com",
]


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
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# -------------------------------------------------
# DATABASE
# -------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
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


# -------------------------------------------------
# STATIC FILES
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# -------------------------------------------------
# MEDIA (IMPORTANT FOR LMS FILES + VIDEOS)
# -------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# -------------------------------------------------
# LOGIN / LOGOUT FLOW
# -------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# -------------------------------------------------
# CRISPY FORMS
# -------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# -------------------------------------------------
# EMAIL (FOR SCHOOL NOTIFICATIONS)
# -------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================
# Email config

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_PASS")


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
            "level": "DEBUG",
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