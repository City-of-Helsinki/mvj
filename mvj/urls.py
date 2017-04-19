import rest_framework.urls
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from users.api import UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include(rest_framework.urls, namespace='rest_framework')),
]
