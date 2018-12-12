from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, router


# This is mostly from Django (django/contrib/auth/management/__init__.py)
def create_permissions(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, apps=global_apps, **kwargs):  # NOQA
    if not app_config.models_module:
        return

    from field_permissions.registry import field_permissions

    app_label = app_config.label
    try:
        app_config = apps.get_app_config(app_label)
        ContentType = apps.get_model('contenttypes', 'ContentType')  # NOQA
        Permission = apps.get_model('auth', 'Permission')  # NOQA
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    # This will hold the permissions we're looking for as
    # (content_type, (codename, name))
    searched_perms = []
    # The codenames and ctypes that should exist.
    ctypes = set()
    for klass in app_config.get_models():
        if not field_permissions.in_registry(klass):
            continue

        # Force looking up the content types in the current database
        # before creating foreign keys to them.
        ctype = ContentType.objects.db_manager(using).get_for_model(klass)

        ctypes.add(ctype)
        for perm in field_permissions.get_field_permissions_for_model(klass):
            searched_perms.append((ctype, perm))

    if not searched_perms:
        return

    # Find all the Permissions that have a content_type for a model we're
    # looking for.  We don't need to check for codenames since we already have
    # a list of the ones we're going to create.
    all_perms = set(
        Permission.objects.using(using).filter(content_type__in=ctypes, ).values_list("content_type", "codename"))

    perms = [Permission(codename=codename, name=name, content_type=ct) for ct, (codename, name) in searched_perms if
             (ct.pk, codename) not in all_perms]

    Permission.objects.using(using).bulk_create(perms)

    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '{}'".format(perm.codename))  # NOQA
