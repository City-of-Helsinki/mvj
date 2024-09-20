import os
import subprocess

import django_stubs_ext
import environ
import sentry_sdk
from django.utils.translation import gettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration

django_stubs_ext.monkeypatch()
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
    DATABASE_URL=(str, "postgis:///mvj"),
    CACHE_URL=(str, "locmemcache://"),
    CONSTANCE_DATABASE_CACHE_BACKEND=(str, ""),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, ""),
    EMAIL_BACKEND=(str, "anymail.backends.mailgun.EmailBackend"),
    DEFAULT_FROM_EMAIL=(str, "mvj@hel.fi"),
    FROM_EMAIL_PLOT_SEARCH=(str, ""),
    FROM_EMAIL_AREA_SEARCH=(str, ""),
    MAILGUN_API_KEY=(str, ""),
    MAILGUN_API_URL=(str, ""),
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
    # See https://www.psycopg.org/psycopg3/docs/api/connections.html#psycopg.Connection.connect for DSN format
    AREA_DATABASE_DSN=(str, "host= port= user= password= dbname="),
    LEASE_AREA_DATABASE_DSN=(str, "host= port= user= password= dbname="),
    AKV_KUVA_LEASE_AREA_DATABASE_DSN=(str, "host= port= user= password= dbname="),
    LASKE_EXPORT_FROM_EMAIL=(str, ""),
    LASKE_EXPORT_ANNOUNCE_EMAIL=(str, ""),
    ASIAKASTIETO_URL=(str, ""),
    ASIAKASTIETO_USER_ID=(str, ""),
    ASIAKASTIETO_PASSWORD=(str, ""),
    ASIAKASTIETO_KEY=(str, ""),
    ASIAKASTIETO_CONSUMER_TARGET_KEY=(str, ""),
    ASIAKASTIETO_COMPANY_TARGET_KEY=(str, ""),
    FACTA_DATABASE_USERNAME=(str, ""),
    FACTA_DATABASE_PASSWORD=(str, ""),
    FACTA_DATABASE_DSN=(str, ""),
    PUBLIC_UI_URL=(str, ""),
    LASKE_EXPORT_HOST=(str, ""),
    LASKE_EXPORT_PORT=(int, ""),
    LASKE_EXPORT_USERNAME=(str, ""),
    LASKE_EXPORT_PASSWORD=(str, ""),
    LASKE_EXPORT_DIRECTORY=(str, ""),
    LASKE_EXPORT_KEY_TYPE=(str, ""),
    LASKE_EXPORT_KEY=(bytes, ""),
    LASKE_PAYMENTS_HOST=(str, ""),
    LASKE_PAYMENTS_PORT=(int, ""),
    LASKE_PAYMENTS_USERNAME=(str, ""),
    LASKE_PAYMENTS_PASSWORD=(str, ""),
    LASKE_PAYMENTS_DIRECTORY=(str, ""),
    LASKE_PAYMENTS_KEY_TYPE=(str, ""),
    LASKE_PAYMENTS_KEY=(bytes, ""),
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
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "modeltranslation",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rangefilter",
    "nested_inline",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_gis",
    "drf_yasg",
    "corsheaders",
    "auditlog",
    "safedelete",
    "sequences.apps.SequencesConfig",
    "django_countries",
    "anymail",
    "users",
    "forms",
    "leasing",
    "plotsearch",
    "laske_export",
    "credit_integration",
    "audittrail",
    "field_permissions",
    "batchrun",
    "constance",
    "sanitized_dump",
    "utils",
    "django_q",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "utils.middleware.CustomAuditlogMiddleware",
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

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
    "DEFAULT_VERSION": "v1",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.oidc.MvjApiTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
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
FROM_EMAIL_PLOT_SEARCH = env.str("FROM_EMAIL_PLOT_SEARCH")
FROM_EMAIL_AREA_SEARCH = env.str("FROM_EMAIL_AREA_SEARCH")

ANYMAIL = {
    "MAILGUN_API_KEY": env.str("MAILGUN_API_KEY"),
    "MAILGUN_API_URL": env.str("MAILGUN_API_URL"),
}

EMAIL_BACKEND = env.str("EMAIL_BACKEND")

CORS_ALLOW_ALL_ORIGINS = True
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

# Enable `{/v1}/pub/helauth/logout/oidc/backchannel/` endpoint
HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED = True

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": env.str("TOKEN_AUTH_ACCEPTED_AUDIENCE"),
    "API_SCOPE_PREFIX": env.str("TOKEN_AUTH_ACCEPTED_SCOPE_PREFIX"),
    "ISSUER": env.str("TOKEN_AUTH_AUTHSERVER_URL"),
    "API_AUTHORIZATION_FIELD": env.str("TOKEN_AUTH_FIELD_FOR_CONSENTS"),
    "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": env.bool("TOKEN_AUTH_REQUIRE_SCOPE_PREFIX"),
}

LASKE_VALUES = {
    "distribution_channel": "10",
    "division": "10",
    "pmntterm": "Z100",
}

LASKE_EXPORT_ROOT = project_root("laske_export_files")

LASKE_DUE_DATE_OFFSET_DAYS = 17

LASKE_SERVERS = {
    "export": {
        "host": env.str("LASKE_EXPORT_HOST"),
        "port": env.int("LASKE_EXPORT_PORT"),
        "username": env.str("LASKE_EXPORT_USERNAME"),
        "password": env.str("LASKE_EXPORT_PASSWORD"),
        "directory": env.str("LASKE_EXPORT_DIRECTORY"),
        "key_type": env.str("LASKE_EXPORT_KEY_TYPE"),
        "key": env.bytes("LASKE_EXPORT_KEY"),
    },
    "payments": {
        "host": env.str("LASKE_PAYMENTS_HOST"),
        "port": env.int("LASKE_PAYMENTS_PORT"),
        "username": env.str("LASKE_PAYMENTS_USERNAME"),
        "password": env.str("LASKE_PAYMENTS_PASSWORD"),
        "directory": env.str("LASKE_PAYMENTS_DIRECTORY"),
        "key_type": env.str("LASKE_PAYMENTS_KEY_TYPE"),
        "key": env.bytes("LASKE_PAYMENTS_KEY"),
    },
}

# See: https://github.com/jjkester/django-auditlog/pull/81
USE_NATIVE_JSONFIELD = True

MVJ_DUE_DATE_OFFSET_DAYS = 17

AREA_DATABASE_DSN = env.str("AREA_DATABASE_DSN")
LEASE_AREA_DATABASE_DSN = env.str("LEASE_AREA_DATABASE_DSN")
AKV_KUVA_LEASE_AREA_DATABASE_DSN = env.str("AKV_KUVA_LEASE_AREA_DATABASE_DSN")

FACTA_DATABASE_USERNAME = env.str("FACTA_DATABASE_USERNAME")
FACTA_DATABASE_PASSWORD = env.str("FACTA_DATABASE_PASSWORD")
FACTA_DATABASE_DSN = env.str("FACTA_DATABASE_DSN")

# Asiakastieto
ASIAKASTIETO_URL = env.str("ASIAKASTIETO_URL")
ASIAKASTIETO_USER_ID = env.str("ASIAKASTIETO_USER_ID")
ASIAKASTIETO_PASSWORD = env.str("ASIAKASTIETO_PASSWORD")
ASIAKASTIETO_KEY = env.str("ASIAKASTIETO_KEY")
ASIAKASTIETO_CONSUMER_TARGET_KEY = env.str("ASIAKASTIETO_CONSUMER_TARGET_KEY")
ASIAKASTIETO_COMPANY_TARGET_KEY = env.str("ASIAKASTIETO_COMPANY_TARGET_KEY")

PUBLIC_UI_URL = env.str("PUBLIC_UI_URL")

local_settings = project_root("local_settings.py")
if os.path.exists(local_settings):
    with open(local_settings) as fp:
        code = compile(fp.read(), local_settings, "exec")
    exec(code, globals(), locals())
