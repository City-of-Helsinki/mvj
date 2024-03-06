from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db.models import OneToOneRel


def recursive_get_related(  # NOQA C901
    obj, user, parent_objs=None, acc=None, exclude_apps=None
):
    """Recursively get objects that relate to `obj`

    Returns all items as {content_type: set(instances)} that are
    related by foreign keys on the `obj` and related objects that
    point to `obj`.

    Checks view_[modelname] permission."""
    if acc is None:
        acc = defaultdict(set)

    if parent_objs is None:
        parent_objs = []

    model = obj.__class__

    # Go through every relation (except the ones marked as skip) and collect
    # all of the referenced items.
    skip_relations = getattr(model, "recursive_get_related_skip_relations", [])

    # relations = (
    #     f for f in model._meta.get_fields(include_hidden=True)
    #     if f.is_relation and f.name not in skip_relations
    # )
    #
    for relation in model._meta.get_fields(include_hidden=True):
        # Exclude apps passed in the first call, to avoid endless recursion
        if exclude_apps is not None and relation.model._meta.app_label in exclude_apps:
            continue

        if (
            not relation.is_relation
            or not relation.name
            or relation.name in skip_relations
        ):
            continue

        accessor_name = relation.name
        if hasattr(relation, "get_accessor_name"):
            accessor_name = relation.get_accessor_name()

        # Skip relations that don't have backwards reference
        if accessor_name.endswith("+"):
            continue

        # Skip relations to a parent model
        if relation.related_model in (po.__class__ for po in parent_objs):
            continue

        if relation.concrete or isinstance(relation, OneToOneRel):
            # Get value as-is if relation is a foreign key or a one-to-one relation
            if not hasattr(obj, accessor_name):
                continue
            concrete_item = getattr(obj, accessor_name)
            if not concrete_item:
                continue
            all_items = [concrete_item]
        else:
            # Otherwise get all instances from the related manager
            related_manager = getattr(obj, accessor_name)

            if not hasattr(related_manager, "all"):
                continue

            # Include soft deleted objects
            if hasattr(related_manager, "all_with_deleted"):
                all_items = related_manager.all_with_deleted()
            else:
                all_items = related_manager.all()

        # Model permission check
        permission_name = (
            f"{relation.model._meta.app_label}.view_{relation.model._meta.model_name}"
        )
        has_permission = user.has_perm(permission_name)

        for item in all_items:
            # Include item only if user has permission, but recurse into sub items regardless
            if has_permission:
                acc[ContentType.objects.get_for_model(item)].add(item)

            parent_objs.append(obj)
            recursive_get_related(
                item,
                user=user,
                parent_objs=parent_objs,
                acc=acc,
                exclude_apps=exclude_apps,
            )
            parent_objs.pop()

    return acc
