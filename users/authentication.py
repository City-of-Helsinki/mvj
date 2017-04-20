from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import authentication, exceptions


class DummyTokenAuthentication(authentication.TokenAuthentication):
    """Authentication where the token string is compared to user names, not any real tokens."""
    def authenticate_credentials(self, key):
        try:
            user = User.objects.get(username=key)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (user, None)
