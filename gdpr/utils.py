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
        user.delete()
