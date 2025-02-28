from django.urls import include, path
from rest_framework import routers

from credit_integration import views

app_name = "credit_integration"


router = routers.DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(
        "get_credit_decisions/",
        views.get_credit_decisions,
        name="get-credit-decisions",
    ),
    path(
        "send_credit_decision_inquiry/",
        views.send_credit_decision_inquiry,
        name="send-credit-decision-inquiry",
    ),
    path(
        "send_sanctions_inquiry/",
        views.send_sanctions_inquiry,
        name="send-sanctions-inquiry",
    ),
]
