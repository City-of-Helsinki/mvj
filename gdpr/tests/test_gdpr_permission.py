from helusers.authz import UserAuthorization
from requests import Request

from gdpr.views import AmrPermission, MvjGDPRAPIView


def test_amr_permission_has_permission():
    request = Request()
    request.auth = UserAuthorization(user=None, api_token_payload={"amr": ["suomi_fi"]})
    view = MvjGDPRAPIView()
    permission = AmrPermission()
    assert permission.has_permission(request, view) is True


def test_amr_permission_has_not_permission():
    request = Request()
    request.auth = UserAuthorization(
        user=None, api_token_payload={"amr": ["helsinki_tunnus"]}
    )
    view = MvjGDPRAPIView()
    permission = AmrPermission()
    assert permission.has_permission(request, view) is False
