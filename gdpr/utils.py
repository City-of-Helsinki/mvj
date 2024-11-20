from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from helsinki_gdpr.views import DryRunException

from users.models import User


def get_user(user: User) -> User:
    """
    Get the user provider, as User is the GDPR API root model. GDPR API implementation
    by default attempts to get it from the root models user attribute.
    This function is used by defining it as the value for setting `GDPR_API_USER_PROVIDER`.
    """
    return user


def delete_user_data(user: User, dry_run: bool) -> None:
    """
    Delete user data.
    """
    if dry_run:
        raise DryRunException("Dry run. Rollback delete transaction.")
    else:
        user_id = user.id
        user.delete()
        content_type = ContentType.objects.get_for_model(User)
        # Create Augitlog entry for deletion of user instance. Store only
        # the object id, ensuring we do not store the personal data that was deleted.
        LogEntry.objects.create(
            content_type=content_type,
            object_pk=str(user_id),
            object_id=user_id,
            object_repr=str(user_id),
            action=LogEntry.Action.DELETE,
            actor=None,
            changes="GDPR API: User data deleted.",
            remote_addr=None,
        )
