import rest_framework.urls
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from leasing.views import AssetViewSet, LeaseViewSet, ktj_proxy

router = routers.DefaultRouter()
router.register(r'asset', AssetViewSet)
router.register(r'lease', LeaseViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace="v1")),
    url(r'(?P<base_type>ktjki[ir])/tuloste/(?P<print_type>[\w/]+)/pdf', ktj_proxy),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include(rest_framework.urls, namespace='rest_framework')),
    url(r'^docs/', get_swagger_view(title='MVJ API')),
]
