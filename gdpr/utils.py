from users.models import User


def get_user(user: User) -> User:
    """
    Get the user provider, as User is the GDPR API root model. GDPR API implementation
    by default attempts to get it from the root models user attribute.
    """
    return user


def delete_user_data(user: User, dry_run: bool) -> None:
    """
    Delete user data.
    """
    user.delete()
