import os
import subprocess

import environ
import sentry_sdk
from django.utils.translation import ugettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration

project_root = environ.Path(__file__) - 2
BASE_DIR = project_root

# Location of the fallback version file, used when no repository is available.
# This is hardcoded as reading it from configuration does not really make
# sense. It is supposed to be a fallback after all.
VERSION_FILE = project_root("../service_state/deployed_version")


def get_git_revision_hash():
    """
    We need a way to retrieve git revision hash for sentry reports
    """
    try:
        # We are not interested in gits complaints, stderr -> null
        git_hash = subprocess.check_output(
            ["git", "describe", "--tags", "--long", "--always"],
            stderr=subprocess.DEVNULL,
            encoding="utf8",
        )
    # First is "git not found", second is most likely "no repository"
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            # fall back to hardcoded file location
            with open(VERSION_FILE) as f:
                git_hash = f.readline()
        except FileNotFoundError:
            git_hash = "revision_not_available"

    return git_hash.rstrip()


env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    ADMINS=(list, []),
    DATABASE_URL=(str, "postgis://mvj:mvj@localhost/mvj"),
    CACHE_URL=(str, "locmemcache://"),
    CONSTANCE_DATABASE_CACHE_BACKEND=(str, ""),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, ""),
    EMAIL_BACKEND=(str, "anymail.backends.sendgrid.EmailBackend"),
    DEFAULT_FROM_EMAIL=(str, "mvj@example.com"),
    SENDGRID_API_KEY=(str, ""),
    KTJ_PRINT_ROOT_URL=(str, "https://ktjws.nls.fi"),
    KTJ_PRINT_USERNAME=(str, ""),
    KTJ_PRINT_PASSWORD=(str, ""),
    CLOUDIA_ROOT_URL=(str, ""),
    CLOUDIA_USERNAME=(str, ""),
    CLOUDIA_PASSWORD=(str, ""),
    VIRRE_API_URL=(str, ""),
    VIRRE_USERNAME=(str, ""),
    VIRRE_PASSWORD=(str, ""),
    NLS_HELSINKI_FOLDER_URL=(str, ""),
    NLS_HELSINKI_USERNAME=(str, ""),
    NLS_HELSINKI_PASSWORD=(str, ""),
    TOKEN_AUTH_ACCEPTED_AUDIENCE=(str, ""),
    TOKEN_AUTH_ACCEPTED_SCOPE_PREFIX=(str, ""),
    TOKEN_AUTH_AUTHSERVER_URL=(str, ""),
    TOKEN_AUTH_FIELD_FOR_CONSENTS=(str, ""),
    TOKEN_AUTH_REQUIRE_SCOPE_PREFIX=(bool, True),
    # See http://initd.org/psycopg/docs/module.html#psycopg2.connect for DSN format
    AREA_DATABASE_DSN=(str, "host= port= user= password= dbname="),
    LEASE_AREA_DATABASE_DSN=(str, "host= port= user= password= dbname="),
    LASKE_EXPORT_FROM_EMAIL=(str, ""),
    LASKE_EXPORT_ANNOUNCE_EMAIL=(str, ""),
)

env_file = project_root(".env")

if os.path.exists(env_file):
    env.read_env(env_file)

DEBUG = env.bool("DEBUG")
SECRET_KEY = env.str("SECRET_KEY", default=("xxx" if DEBUG else ""))

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

ADMINS = env.list("ADMINS")

DATABASES = {"default": env.db()}

CACHES = {"default": env.cache()}

if env("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        environment=env("SENTRY_ENVIRONMENT"),
        release=get_git_revision_hash(),
        integrations=[DjangoIntegration()],
    )

MEDIA_ROOT = project_root("media")
STATIC_ROOT = project_root("static")
MEDIA_URL = "/media/"
STATIC_URL = "/static/"

ROOT_URLCONF = "mvj.urls"
WSGI_APPLICATION = "mvj.wsgi.application"

LANGUAGE_CODE = "fi"
LANGUAGES = [
    ("fi", _("Finnish")),
    ("sv", _("Swedish")),
    ("en", _("English")),
]
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [project_root("locale")]

INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rangefilter",
    "helusers",
    "crispy_forms",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_gis",
    "rest_framework_swagger",
    "corsheaders",
    "auditlog",
    "safedelete",
    "sequences",
    "django_countries",
    "anymail",
    "users",
    "forms",
    "leasing",
    "laske_export",
    "field_permissions",
    "batchrun",
    "django_q",
    "constance",
    "constance.backends.database",
    "sanitized_dump",
    "utils",
]

if DEBUG:
    INSTALLED_APPS += ["django_extensions"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

AUTH_USER_MODEL = "users.User"

MODELTRANSLATION_TRANSLATION_FILES = ("forms.translation",)

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_DATABASE_CACHE_BACKEND = env.str("CONSTANCE_DATABASE_CACHE_BACKEND")
CONSTANCE_CONFIG = {
    "LASKE_EXPORT_FROM_EMAIL": (
        env.str("LASKE_EXPORT_FROM_EMAIL"),
        _("Sender email address. Example: john@example.com"),
    ),
    "LASKE_EXPORT_ANNOUNCE_EMAIL": (
        env.str("LASKE_EXPORT_ANNOUNCE_EMAIL"),
        _("Recipients of announce emails. Example: john@example.com,jane@example.com"),
    ),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "Laske Export": ("LASKE_EXPORT_FROM_EMAIL", "LASKE_EXPORT_ANNOUNCE_EMAIL"),
}

# Required by django-helusers
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": ("v1",),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "helusers.oidc.ApiTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "leasing.permissions.MvjDjangoModelPermissions",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "leasing.renderers.BrowsableAPIRendererWithoutForms",
    ],
    "DEFAULT_METADATA_CLASS": "leasing.metadata.FieldsMetadata",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 30,
    "EXCEPTION_HANDLER": "leasing.viewsets.utils.integrityerror_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
}

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
MVJ_EMAIL_FROM = DEFAULT_FROM_EMAIL

ANYMAIL = {"SENDGRID_API_KEY": env.str("SENDGRID_API_KEY")}

EMAIL_BACKEND = env.str("EMAIL_BACKEND")

CORS_ORIGIN_ALLOW_ALL = True
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

Q_CLUSTER = {
    "name": "DjangORM",
    "timeout": 90,
    "retry": 60 * 60,  # 1 hour
    "orm": "default",
}

KTJ_PRINT_ROOT_URL = env.str("KTJ_PRINT_ROOT_URL")
KTJ_PRINT_USERNAME = env.str("KTJ_PRINT_USERNAME")
KTJ_PRINT_PASSWORD = env.str("KTJ_PRINT_PASSWORD")

CLOUDIA_ROOT_URL = env.str("CLOUDIA_ROOT_URL")
CLOUDIA_USERNAME = env.str("CLOUDIA_USERNAME")
CLOUDIA_PASSWORD = env.str("CLOUDIA_PASSWORD")

VIRRE_API_URL = env.str("VIRRE_API_URL")
VIRRE_USERNAME = env.str("VIRRE_USERNAME")
VIRRE_PASSWORD = env.str("VIRRE_PASSWORD")

NLS_HELSINKI_FOLDER_URL = env.str("NLS_HELSINKI_FOLDER_URL")
NLS_HELSINKI_USERNAME = env.str("NLS_HELSINKI_USERNAME")
NLS_HELSINKI_PASSWORD = env.str("NLS_HELSINKI_PASSWORD")
NLS_IMPORT_ROOT = project_root("nls_leasehold_transfers")

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": env.str("TOKEN_AUTH_ACCEPTED_AUDIENCE"),
    "API_SCOPE_PREFIX": env.str("TOKEN_AUTH_ACCEPTED_SCOPE_PREFIX"),
    "ISSUER": env.str("TOKEN_AUTH_AUTHSERVER_URL"),
    "API_AUTHORIZATION_FIELD": env.str("TOKEN_AUTH_FIELD_FOR_CONSENTS"),
    "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": env.bool("TOKEN_AUTH_REQUIRE_SCOPE_PREFIX"),
}

LASKE_VALUES = {
    "sender_id": "ID340",
    "import_id": "ID256",
    "sales_org": "2800",
    "distribution_channel": "10",
    "division": "10",
    "pmntterm": "Z100",
}

LASKE_EXPORT_ROOT = project_root("laske_export_files")

LASKE_DUE_DATE_OFFSET_DAYS = 17

LASKE_SERVERS = {
    "export": {
        "host": "localhost",
        "port": 22,
        "username": "",
        "password": "",
        "directory": "./",
        "key_type": "",
        "key": b"",
    },
    "payments": {
        "host": "",
        "port": 22,
        "username": "",
        "password": "",
        "directory": "",
        "key_type": "",
        "key": b"",
    },
}

# See: https://github.com/jjkester/django-auditlog/pull/81
USE_NATIVE_JSONFIELD = True

MVJ_DUE_DATE_OFFSET_DAYS = 17

AREA_DATABASE_DSN = env.str("AREA_DATABASE_DSN")
LEASE_AREA_DATABASE_DSN = env.str("LEASE_AREA_DATABASE_DSN")

local_settings = project_root("local_settings.py")
if os.path.exists(local_settings):
    with open(local_settings) as fp:
        code = compile(fp.read(), local_settings, "exec")
    exec(code, globals(), locals())
