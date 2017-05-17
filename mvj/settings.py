import os

import environ
import raven

project_root = environ.Path(__file__) - 2

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    ADMINS=(list, []),
    DATABASE_URL=(str, 'postgres://mvj:mvj@localhost/mvj'),
    CACHE_URL=(str, 'locmemcache://'),
    EMAIL_URL=(str, 'consolemail://'),
    SENTRY_DSN=(str, ''),
)

env_file = project_root('.env')

if os.path.exists(env_file):
    env.read_env(env_file)

DEBUG = env.bool('DEBUG')
SECRET_KEY = env.str('SECRET_KEY', default=('xxx' if DEBUG else ''))

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

ADMINS = env.list('ADMINS')

DATABASES = {
    'default': env.db()
}

CACHES = {
    'default': env.cache()
}

vars().update(env.email_url())  # EMAIL_BACKEND etc.

try:
    version = raven.fetch_git_sha(project_root())
except Exception:
    version = None

RAVEN_CONFIG = {'dsn': env.str('SENTRY_DSN'), 'release': version}

MEDIA_ROOT = project_root('media')
STATIC_ROOT = project_root('static')
MEDIA_URL = "/media/"
STATIC_URL = "/static/"

ROOT_URLCONF = 'mvj.urls'
WSGI_APPLICATION = 'mvj.wsgi.application'

LANGUAGE_CODE = 'fi'
TIME_ZONE = 'Europe/Helsinki'
USE_I18N = True
USE_L10N = True
USE_TZ = True


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'crispy_forms',
    'django_filters',
    'rest_framework',
    'corsheaders',
    'rest_framework_swagger',

    'leasing',
    'users',
]
if RAVEN_CONFIG['dsn']:
    INSTALLED_APPS += ['raven.contrib.django.raven_compat']

if DEBUG:
    INSTALLED_APPS += [
        'django_extensions',
    ]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'ALLOWED_VERSIONS': ('v1',),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.DummyTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_METADATA_CLASS': 'leasing.metadata.FieldsMetadata',
}

CORS_ORIGIN_ALLOW_ALL = True

local_settings = project_root('local_settings.py')
if os.path.exists(local_settings):
    with open(local_settings) as fp:
        code = compile(fp.read(), local_settings, 'exec')
    exec(code, globals(), locals())
