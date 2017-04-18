import os

import environ

project_root = environ.Path(__file__) - 2

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, 'postgres://mvj:mvj@localhost/mvj'),
    CACHE_URL=(str, 'locmemcache://'),
    EMAIL_URL=(str, 'consolemail://'),
)

env_file = project_root('.env')

if os.path.exists(env_file):
    env.read_env(env_file)

DEBUG = env.bool('DEBUG')
SECRET_KEY = env.str('SECRET_KEY')

if DEBUG and not SECRET_KEY:
    SECRET_KEY = 'xxx'

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': env.db()
}

CACHES = {
    'default': env.cache()
}

vars().update(env.email_url())  # EMAIL_BACKEND etc.

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

    'leasing',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}
