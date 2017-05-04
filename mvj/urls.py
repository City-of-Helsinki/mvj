import rest_framework.urls
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from leasing.views import ApplicationViewSet, ContactViewSet, DecisionViewSet, LeaseViewSet, RentViewSet, TenantViewSet
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'user', UserViewSet)
router.register(r'application', ApplicationViewSet)
router.register(r'lease', LeaseViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'decision', DecisionViewSet)
router.register(r'rent', RentViewSet)
router.register(r'tenant', TenantViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace="v1")),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include(rest_framework.urls, namespace='rest_framework')),
]
