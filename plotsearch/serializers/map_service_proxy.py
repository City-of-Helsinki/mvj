from rest_framework import serializers


class WmsRequestSerializer(serializers.Serializer):
    """Serializer for validating WMS request parameters."""

    bbox = serializers.CharField(required=True)
    srs = serializers.CharField(required=False, default="EPSG:3879")
    width = serializers.IntegerField(
        required=False, min_value=1, max_value=4096, default=256
    )
    height = serializers.IntegerField(
        required=False, min_value=1, max_value=4096, default=256
    )
    format = serializers.ChoiceField(
        required=False, choices=["image/png", "image/jpeg"], default="image/png"
    )

    def validate_bbox(self, bbox: str):
        """
        Validate the format of the bounding box (bbox) string.

        Args:
            value (str): A string representing the bounding box, expected to be
                         a comma-separated list of four numeric values.
                         In format: "min_x,min_y,max_x,max_y".

        Returns:
            str: The validated bbox string if it meets the required format.

        Raises:
            serializers.ValidationError: If the bbox does not contain exactly
                                         four comma-separated values or if any
                                         value is not a valid numeric type.
        """
        parts = bbox.split(",")
        if len(parts) != 4:
            raise serializers.ValidationError(
                "bbox must contain exactly 4 comma-separated values"
            )
        for i, part in enumerate(parts):
            try:
                float(part)
            except ValueError:
                raise serializers.ValidationError(
                    f"Invalid numeric value in bbox index {i}: '{part}'"
                )

        return bbox

    def validate_srs(self, srs: str):
        """
        Validate the Spatial Reference System (SRS) format.

        Args:
            value (str): The SRS value to validate, expected to be in the format "EPSG:<number>".

        Returns:
            str: The validated SRS value if it matches the expected format.

        Raises:
            serializers.ValidationError: If the SRS value does not match the "EPSG:<number>" format.
        """
        if not srs:
            return None
        if not srs.upper().startswith("EPSG:"):
            raise serializers.ValidationError("SRS must start with 'EPSG:'")

        srs_code = srs[5:]

        if not srs_code:
            raise serializers.ValidationError("Missing EPSG code number")

        try:
            int(srs_code)
        except ValueError:
            raise serializers.ValidationError(f"Invalid EPSG code number: '{srs_code}'")

        return srs
