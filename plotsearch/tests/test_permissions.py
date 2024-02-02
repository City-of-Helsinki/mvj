import pytest
from requests import Request

from conftest import UserFactory
from forms.models import Answer
from plotsearch.models.plot_search import AreaSearch
from plotsearch.permissions import AreaSearchPublicPermissions


@pytest.mark.django_db
def test_area_search_public_permissions__answered_is_not_allowed():
    area_search = AreaSearch()
    area_search.answer = Answer()
    permission = AreaSearchPublicPermissions()
    has_permission = permission.has_object_permission(None, None, area_search)
    assert has_permission is False


@pytest.mark.django_db
def test_area_search_public_permissions__user_check():
    user = UserFactory()
    request = Request()
    request.user = user
    area_search = AreaSearch()
    area_search.user = user
    permission = AreaSearchPublicPermissions()
    has_permission = permission.has_object_permission(request, None, area_search)
    assert has_permission is True

    area_search.user = UserFactory()
    has_permission = permission.has_object_permission(request, None, area_search)
    assert has_permission is False
