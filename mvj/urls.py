import rest_framework.urls
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework_nested import routers

from leasing.views import ApplicationViewSet, ContactViewSet, DecisionViewSet, LeaseViewSet, RentViewSet, TenantViewSet
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'leases', LeaseViewSet)
router.register(r'contacts', ContactViewSet)

leases_router = routers.NestedSimpleRouter(router, r'leases', lookup='lease')
leases_router.register(r'decisions', DecisionViewSet, base_name='lease-decisions')
leases_router.register(r'rents', RentViewSet, base_name='lease-rents')
leases_router.register(r'tenants', TenantViewSet, base_name='lease-tenants')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace="v1")),
    url(r'^v1/', include(leases_router.urls, namespace="v1")),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include(rest_framework.urls, namespace='rest_framework')),
]
