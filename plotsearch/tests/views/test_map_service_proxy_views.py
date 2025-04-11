from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.conf import settings
from django.urls import reverse
from django.utils import translation
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_504_GATEWAY_TIMEOUT,
)

from plotsearch.serializers.map_service_proxy import WmsRequestSerializer
from plotsearch.views.map_service_proxy import helsinki_owned_areas_wms_proxy


@pytest.fixture
def valid_request_data():
    return {
        "format": "image/png",
        "width": 256,
        "height": 256,
        "srs": "EPSG:4326",
        "bbox": "24.93545,60.16952,24.94545,60.17952",
    }


@pytest.fixture
def mock_settings():
    settings.MAP_SERVICE_WMS_URL = "http://example.com/wms"
    settings.MAP_SERVICE_WMS_USERNAME = "test_user"
    settings.MAP_SERVICE_WMS_PASSWORD = "test_password"
    settings.MAP_SERVICE_WMS_HELSINKI_OWNED_AREAS_LAYER = "test_layer"


def test_missing_configuration(rf):
    with patch("plotsearch.views.map_service_proxy.settings") as mock_settings:
        mock_settings.MAP_SERVICE_WMS_URL = None
        url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
        request = rf.get(url)
        response = helsinki_owned_areas_wms_proxy(request)
        assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == "Service misconfigured."


def test_invalid_serializer(rf, mock_settings):
    url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
    request = rf.get(url, {"format": "image/png"})
    response = helsinki_owned_areas_wms_proxy(request)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "bbox" in response.data.keys(), "bbox is required in request"


@patch("plotsearch.views.map_service_proxy.requests.get")
@patch("plotsearch.views.map_service_proxy.WmsRequestSerializer")
def test_request_timeout(
    mock_serializer, mock_requests, rf, valid_request_data, mock_settings
):
    mock_serializer.return_value.is_valid.return_value = True
    mock_serializer.return_value.validated_data = valid_request_data
    mock_requests.side_effect = requests.exceptions.Timeout

    url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
    request = rf.get(url, valid_request_data)
    response = helsinki_owned_areas_wms_proxy(request)
    assert response.status_code == HTTP_504_GATEWAY_TIMEOUT
    assert response.data == "Error connecting to map service, timeout"


@patch("plotsearch.views.map_service_proxy.requests.get")
@patch("plotsearch.views.map_service_proxy.WmsRequestSerializer")
def test_upstream_service_error(
    mock_serializer, mock_requests, rf, valid_request_data, mock_settings
):
    mock_serializer.return_value.is_valid.return_value = True
    mock_serializer.return_value.validated_data = valid_request_data
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.content = b"Upstream error"
    mock_requests.return_value = mock_response

    url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
    request = rf.get(url, valid_request_data)
    response = helsinki_owned_areas_wms_proxy(request)
    assert response.status_code == 500
    with translation.override("en"):
        assert response.data == "Error in upstream service"


@patch("plotsearch.views.map_service_proxy.requests.get")
@patch("plotsearch.views.map_service_proxy.WmsRequestSerializer")
def test_successful_proxy(
    mock_serializer, mock_requests, rf, valid_request_data, mock_settings
):
    mock_serializer.return_value.is_valid.return_value = True
    mock_serializer.return_value.validated_data = valid_request_data

    mock_fields = MagicMock()
    mock_format_field = MagicMock()
    choices = WmsRequestSerializer().fields.fields.get("format").choices
    mock_format_field.choices = choices

    mock_fields.get.return_value = mock_format_field

    mock_serializer.return_value.fields = MagicMock()
    mock_serializer.return_value.fields.fields = mock_fields

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "image/png"}
    mock_response.raw = BytesIO(b"image data")
    mock_requests.return_value = mock_response

    url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
    request = rf.get(url, valid_request_data)
    response = helsinki_owned_areas_wms_proxy(request)
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    content = b"".join(list(response.streaming_content))
    assert content == b"image data"


@patch("plotsearch.views.map_service_proxy.requests.get")
@patch("plotsearch.views.map_service_proxy.WmsRequestSerializer")
def test_invalid_content_type_from_upstream(
    mock_serializer, mock_requests, rf, valid_request_data, mock_settings
):
    mock_serializer.return_value.is_valid.return_value = True
    mock_serializer.return_value.validated_data = valid_request_data
    mock_format_field = MagicMock()
    choices = WmsRequestSerializer().fields.fields.get("format").choices
    mock_format_field.choices = choices
    mock_fields = MagicMock()
    mock_fields.get.return_value = mock_format_field
    mock_serializer.return_value.fields = MagicMock()
    mock_serializer.return_value.fields.fields = mock_fields

    mock_response = MagicMock()
    mock_response.status_code = HTTP_200_OK
    mock_response.headers = {"Content-Type": "text/html"}  # Not in allowed formats
    mock_response.raw = BytesIO(b"<html><body>Not an image</body></html>")
    mock_requests.return_value = mock_response

    url = reverse("v1:pub_helsinki_owned_areas_wms_proxy")
    request = rf.get(url, valid_request_data)

    with translation.override("en"):
        response = helsinki_owned_areas_wms_proxy(request)

        assert response.status_code == HTTP_502_BAD_GATEWAY
        assert response.data == "Invalid response from upstream service"

        mock_logger = MagicMock()
        with patch("plotsearch.views.map_service_proxy.logger", mock_logger):
            helsinki_owned_areas_wms_proxy(request)
            mock_logger.warning.assert_called_once_with(
                "Unexpected content type from upstream: text/html"
            )
