import os
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_django_manage_py(max_depth: int = 3) -> str:
    manage_py_path = getattr(settings, 'MANAGE_PY_PATH', None)
    if manage_py_path:
        if not isinstance(manage_py_path, str):
            raise ImproperlyConfigured('MANAGE_PY_PATH should be a string')
        return manage_py_path

    # Try to auto detect by searching down from dir containing settings
    settings_mod = sys.modules[settings.SETTINGS_MODULE]  # type: ignore
    directory = os.path.dirname(settings_mod.__file__)
    tries_left = max_depth
    while directory != '/' and tries_left:
        candidate = os.path.join(directory, 'manage.py')
        if os.path.exists(candidate):
            return candidate
        tries_left -= 1
        directory = os.path.dirname(directory)
    raise EnvironmentError('Cannot find manage.py')
