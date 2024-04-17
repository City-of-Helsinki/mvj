from rest_framework import serializers

from plotsearch.models import TargetInfoLink


class PlotSearchTargetInfoLinkSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        read_only=False,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = TargetInfoLink
        fields = (
            "id",
            "url",
            "description",
            "language",
        )
