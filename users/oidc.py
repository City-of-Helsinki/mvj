from django.core.cache import cache
from django.db import DatabaseError, IntegrityError
from helusers.authz import UserAuthorization
from helusers.oidc import ApiTokenAuthentication

from users.models import User


class MvjApiTokenAuthentication(ApiTokenAuthentication):
    def authenticate(self, request):
        result: tuple[User | None, UserAuthorization] = super().authenticate(request)

        if not result:
            return

        user, auth = result
        # Update users service units every 10 minutes
        if user and user.id:
            cache_key = f"service_units_updated_user_{user.id}"
            cache_value = cache.get(cache_key)
            if not cache_value:
                # Set cache before `update_service_units()` to prevent multiple updates
                cache.set(cache_key, True, timeout=600)  # 10 minutes
                try:
                    user.update_service_units()
                except (IntegrityError, DatabaseError):
                    cache.delete(cache_key)

        return user, auth
