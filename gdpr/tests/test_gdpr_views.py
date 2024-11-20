import pytest
from helusers.authz import UserAuthorization
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from gdpr.views import MvjGDPRAPIView
from plotsearch.enums import InformationCheckName


def _find_matching_dicts(data: list, key: str, match_value: str) -> list:
    """
    Recursively find all dictionaries in a nested structure that match the key-value pair.
    """
    matches = []
    if isinstance(data, dict):
        if data.get(key) == match_value:
            matches.append(data)
        for value in data.values():
            matches.extend(_find_matching_dicts(value, key, match_value))
    elif isinstance(data, list):
        for item in data:
            matches.extend(_find_matching_dicts(item, key, match_value))
    return matches


@pytest.mark.django_db
def test_api_get_user_data(
    settings,
    user_factory,  # users
    area_search_factory,  # plotsearch
    area_search_attachment_factory,  # plotsearch
):
    settings.GDPR_API_QUERY_SCOPE = "gdprquery"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes",
    }

    user = user_factory(first_name="Etunimi", last_name="Sukunimi")
    areasearch = area_search_factory(user=user, description_area="Test")
    areasearch_attachment = area_search_attachment_factory(
        user=user, area_search=areasearch, name="king_of_finland.txt"
    )
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.get(f"/v1/pub/gdpr-api/v1/profiles/{user.uuid}")
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "amr": ["suomi_fi"],
            "authorization": {"permissions": {"scopes": ["gdprquery"]}},
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = MvjGDPRAPIView.as_view()(request, uuid=user.uuid)

    assert response.status_code == status.HTTP_200_OK

    user_data_dicts = {
        x.get("key"): x.get("value")
        for x in response.data.get("children")
        if isinstance(x, dict)
    }
    assert user_data_dicts.get("FIRST_NAME") == "Etunimi"
    assert user_data_dicts.get("LAST_NAME") == "Sukunimi"

    areasearchattachments = _find_matching_dicts(
        response.data.get("children"), "key", "AREASEARCHATTACHMENT"
    )
    areasearchattachment_name = _find_matching_dicts(
        areasearchattachments, "key", "NAME"
    )[0]["value"]
    assert areasearchattachment_name == areasearch_attachment.name


@pytest.mark.django_db
def test_api_get_user_data_invalid_scope(
    settings,
    user_factory,  # users
):
    settings.GDPR_API_QUERY_SCOPE = "gdprquery"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes",
    }

    user = user_factory()
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.get(f"/v1/pub/gdpr-api/v1/profiles/{user.uuid}")
    scopes = ["invalidscope"]
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "amr": ["suomi_fi"],
            "authorization": {"permissions": {"scopes": scopes}},
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = MvjGDPRAPIView.as_view()(request, uuid=user.uuid)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_delete_user_data(
    settings,
    user_factory,  # users
    area_search_factory,  # plotsearch
):
    settings.GDPR_API_DELETE_SCOPE = "gdprdelete"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes",
    }

    user = user_factory(first_name="Etunimi", last_name="Sukunimi")
    areasearch = area_search_factory(user=user, description_area="Test")
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.delete(f"/v1/pub/gdpr-api/v1/profiles/{user.uuid}")
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "amr": ["suomi_fi"],
            "authorization": {"permissions": {"scopes": ["gdprdelete"]}},
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = MvjGDPRAPIView.as_view()(request, uuid=user.uuid)

    # Expect deletion to be successful
    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(user.DoesNotExist):
        user.refresh_from_db()

    areasearch.refresh_from_db()
    assert areasearch.user is None


@pytest.mark.django_db
def test_api_delete_user_data_not_possible(
    settings,
    user_factory,  # users
    information_check_factory,  # plotsearch
):
    settings.GDPR_API_DELETE_SCOPE = "gdprdelete"
    settings.OIDC_API_TOKEN_AUTH = {
        "API_AUTHORIZATION_FIELD": "authorization.permissions.scopes2",
    }

    user = user_factory()
    # IMPORTANT: This model is not expected to be related to a user that would be doing
    # a GDPR API delete. It is used simply for demonstration purposes, as the model
    # has `on_delete=models.PROTECT` for the `preparer` field that refers to a `User` instance.
    information_check = information_check_factory(
        preparer=user, name=InformationCheckName.CREDITWORTHINESS
    )
    apirequest_factory = APIRequestFactory()
    request = apirequest_factory.delete(f"/v1/pub/gdpr-api/v1/profiles/{user.uuid}")
    user_authorization = UserAuthorization(
        user=user,
        api_token_payload={
            "amr": ["suomi_fi"],
            "authorization": {"permissions": {"scopes": ["gdprdelete"]}},
        },
    )
    force_authenticate(request, user=user, token=user_authorization)

    response = MvjGDPRAPIView.as_view()(request, uuid=user.uuid)

    # Expect the request to fail due to on_delete=models.PROTECT on InformationCheck.preparer
    # Deletion of the user object is therefore not possible.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert information_check.preparer == user
