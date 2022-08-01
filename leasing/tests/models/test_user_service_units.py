import json
from time import time

import pytest
from Cryptodome.PublicKey import RSA
from django.contrib.auth.models import Permission
from django.urls import reverse
from helusers.models import ADGroup, ADGroupMapping
from httpretty import httprettified, httpretty
from jwkest.jwk import RSAKey
from jwkest.jws import JWS

from leasing.models.service_unit import ServiceUnitGroupMapping

OIDC_ISSUER = "https://example.com/openid"
JWKS_URI = "https://example.com/openid/jwks"


@pytest.mark.django_db
@httprettified
def test_api_access_updates_service_units(
    settings, client, user, lease_test_data, group
):
    """Test that the service units are updated when the user accesses the API
    using a JWT"""
    # User and permissions
    permission = Permission.objects.get(codename="view_lease")
    user.user_permissions.add(permission)
    service_unit = lease_test_data["lease"].service_unit
    ad_group_name = "test_ad_group"
    ad_group = ADGroup.objects.create(name=ad_group_name)
    ADGroupMapping.objects.create(group=group, ad_group=ad_group)
    ServiceUnitGroupMapping.objects.create(group=group, service_unit=service_unit)

    # Generate JWT and setup httpretty
    rsa_key = RSA.generate(2048)
    rsa_jwk = RSAKey(kid="rsa1", key=rsa_key)

    settings.OIDC_API_TOKEN_AUTH["ISSUER"] = OIDC_ISSUER
    settings.OIDC_API_TOKEN_AUTH["AUDIENCE"] = "test_client_id"
    settings.OIDC_API_TOKEN_AUTH["API_AUTHORIZATION_FIELD"] = "test_api_host"
    settings.OIDC_API_TOKEN_AUTH["API_SCOPE_PREFIX"] = "test_prefix"

    # Reload helusers api token auth settings after the settings are changed
    from helusers.settings import api_token_auth_settings

    api_token_auth_settings._load()

    httpretty.register_uri(
        httpretty.GET,
        f"{OIDC_ISSUER}/.well-known/openid-configuration",
        body=json.dumps({"issuer": OIDC_ISSUER, "jwks_uri": JWKS_URI}),
        content_type="application/json",
    )

    httpretty.register_uri(
        httpretty.GET, JWKS_URI, body=json.dumps({"keys": [rsa_jwk.serialize()]}),
    )

    time_now = time()
    payload = json.dumps(
        {
            "iss": OIDC_ISSUER,
            "sub": str(user.uuid),
            "aud": settings.OIDC_API_TOKEN_AUTH["AUDIENCE"],
            "exp": time_now + 600,
            "iat": time_now,
            "auth_time": time_now,
            "name": "Test User",
            "given_name": "Test",
            "family_name": "User",
            "email": "test_user@example.com",
            "ad_groups": [ad_group_name],
            "azp": settings.OIDC_API_TOKEN_AUTH["AUDIENCE"],
            settings.OIDC_API_TOKEN_AUTH["API_AUTHORIZATION_FIELD"]: [
                settings.OIDC_API_TOKEN_AUTH["API_SCOPE_PREFIX"],
            ],
        }
    )
    signature = JWS(payload, alg="RS256")
    jwt_token = signature.sign_compact([rsa_jwk])

    url = reverse("lease-detail", kwargs={"pk": lease_test_data["lease"].id})
    response = client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_token}")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert user.service_units.count() == 1


@pytest.mark.django_db
def test_service_unit_update_on_login(client, user_factory, service_unit, group):
    """Test that the service units are updated when the user logs into the
    browsable REST API or into the Admin."""
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()

    ServiceUnitGroupMapping.objects.create(group=group, service_unit=service_unit)
    user.service_units.add(service_unit)

    client.login(username="test_user", password="test_password")

    assert user.service_units.count() == 0
