import pytest
from rest_framework.exceptions import ValidationError

from plotsearch.serializers.map_service_proxy import WmsRequestSerializer


def test_validate_bbox_valid():
    serializer = WmsRequestSerializer()
    valid_bbox = "24.93545,60.16952,24.94545,60.17952"
    assert serializer.validate_bbox(valid_bbox) == valid_bbox


def test_validate_bbox_invalid_format():
    serializer = WmsRequestSerializer()
    invalid_bbox = "24.93545,60.16952,24.94545"
    with pytest.raises(
        ValidationError, match="bbox must contain exactly 4 comma-separated values"
    ):
        serializer.validate_bbox(invalid_bbox)


def test_validate_bbox_invalid_numeric_value():
    serializer = WmsRequestSerializer()
    invalid_bbox = "24.93545,60.16952,24.94545,invalid"
    with pytest.raises(
        ValidationError, match="Invalid numeric value in bbox index 3: 'invalid'"
    ):
        serializer.validate_bbox(invalid_bbox)


def test_validate_srs_valid():
    serializer = WmsRequestSerializer()
    valid_srs = "EPSG:4326"
    assert serializer.validate_srs(valid_srs) == valid_srs


def test_validate_srs_missing_epsg_code():
    serializer = WmsRequestSerializer()
    invalid_srs = "EPSG:"
    with pytest.raises(ValidationError, match="Missing EPSG code number"):
        serializer.validate_srs(invalid_srs)


def test_validate_srs_invalid_format():
    serializer = WmsRequestSerializer()
    invalid_srs = "INVALID:4326"
    with pytest.raises(ValidationError, match="SRS must start with 'EPSG:'"):
        serializer.validate_srs(invalid_srs)


def test_validate_srs_invalid_epsg_code():
    serializer = WmsRequestSerializer()
    invalid_srs = "EPSG:abcd"
    with pytest.raises(ValidationError, match="Invalid EPSG code number: 'abcd'"):
        serializer.validate_srs(invalid_srs)
