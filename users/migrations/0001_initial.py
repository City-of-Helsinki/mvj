from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password
from django.core.management import call_command
from django.db import migrations


def load_users_from_fixture(apps, schema_editor):
    call_command('loaddata', 'users', verbosity=0, interactive=False)
    user_model = apps.get_model('auth.User')
    users = user_model.objects.filter(email__contains='@autocreated.invalid')
    for user in users:
        user._password = user.username
        user.password = make_password(user.username)
        user.save()


def delete_autocreated_users(apps, schema_editor):
    user_model = apps.get_model('auth.User')
    users = user_model.objects.filter(email__contains='@autocreated.invalid')
    users.delete()


class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunPython(
            code=load_users_from_fixture,
            reverse_code=delete_autocreated_users),
    ]
