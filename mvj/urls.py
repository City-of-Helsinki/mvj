import rest_framework.urls
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from leasing.views import AssetViewSet, LeaseViewSet, ktj_proxy

router = routers.DefaultRouter()
router.register(r'asset', AssetViewSet)
router.register(r'lease', LeaseViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
    re_path(r'(?P<base_type>ktjki[ir])/tuloste/(?P<print_type>[\w/]+)/pdf', ktj_proxy),
    path('admin/', admin.site.urls),
    path('auth/', include(rest_framework.urls)),
    path('docs/', get_swagger_view(title='MVJ API')),
]
