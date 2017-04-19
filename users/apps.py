import django.apps


class UsersConfig(django.apps.AppConfig):
    name = __name__.rsplit('.', 1)[0]
