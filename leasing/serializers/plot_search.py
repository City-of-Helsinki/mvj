from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import PlotSearchTargetType
from leasing.models import (
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
)
from leasing.serializers.utils import NameModelSerializer
from users.models import User
from users.serializers import UserSerializer

from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class PlotSearchSubtypeSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchSubtype
        fields = "__all__"


class PlotSearchStageSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchStage
        fields = "__all__"


class PlotSearchTargetSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()
    target_type = EnumField(enum=PlotSearchTargetType)

    class Meta:
        model = PlotSearchTarget
        fields = ("id", "plan_unit", "target_type")


class PlotSearchTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchType
        fields = "__all__"


class PlotSearchListSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer()
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchRetrieveSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer()
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()
    preparer = UserSerializer()
    targets = PlotSearchTargetSerializer(many=True, read_only=True)

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )
    targets = PlotSearchTargetSerializer(
        source="plotsearchtarget_set", many=True, required=False
    )

    class Meta:
        model = PlotSearch
        fields = "__all__"

    def create(self, validated_data):
        targets = validated_data.pop("plotsearchtarget_set")
        plot_search = PlotSearch.objects.create(**validated_data)

        for target in targets:
            plot_search_target = PlotSearchTarget.objects.create(
                plot_search=plot_search,
                plan_unit=target.get("plan_unit"),
                target_type=target.get("target_type"),
            )
            plot_search_target.save()

        return plot_search

    def update(self, instance, validated_data):
        targets = validated_data.pop("plotsearchtarget_set")
        for item in validated_data:
            if PlotSearch._meta.get_field(item):
                setattr(instance, item, validated_data[item])
        PlotSearchTarget.objects.filter(plot_search=instance).delete()
        for target in targets:
            d = dict(target)
            PlotSearchTarget.objects.create(
                plot_search=instance, plan_unit=d["plan_unit"]
            )
        instance.save()
        return instance

    def validate(self, attrs):
        targets = attrs.get("plotsearchtarget_set")
        for target in targets:
            instance = PlotSearchTarget(**target)
            instance.clean()
        return attrs


class PlotSearchCreateSerializer(PlotSearchUpdateSerializer):
    class Meta:
        model = PlotSearch
        fields = "__all__"
