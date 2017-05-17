import rest_framework.urls
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from leasing.views import (
    ApplicationViewSet, AreaViewSet, ContactViewSet, DecisionViewSet, InvoiceViewSet, LeaseViewSet, NoteViewSet,
    RentViewSet, TenantViewSet)
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'application', ApplicationViewSet)
router.register(r'area', AreaViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'decision', DecisionViewSet)
router.register(r'invoice', InvoiceViewSet)
router.register(r'lease', LeaseViewSet)
router.register(r'note', NoteViewSet)
router.register(r'rent', RentViewSet)
router.register(r'tenant', TenantViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace="v1")),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include(rest_framework.urls, namespace='rest_framework')),
    url(r'^docs/', get_swagger_view(title='MVJ API')),
]
