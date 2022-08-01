from django.core.cache import cache
from helusers.oidc import ApiTokenAuthentication


class MvjApiTokenAuthentication(ApiTokenAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)

        if not result:
            return

        user, auth = result

        # Update users service units every 10 minutes
        if user and user.id:
            cache_key = f"service_units_updated_user_{user.id}"
            if not cache.get(cache_key):
                user.update_service_units()
                cache.set(cache_key, True, timeout=600)  # 10 minutes

        return user, auth
