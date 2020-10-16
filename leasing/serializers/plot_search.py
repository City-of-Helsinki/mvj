from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
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
    is_master_plan_unit_deleted = serializers.SerializerMethodField()
    is_master_plan_unit_newer = serializers.ReadOnlyField(
        source="plan_unit.is_master_newer"
    )
    message_label = serializers.SerializerMethodField()

    class Meta:
        model = PlotSearchTarget
        fields = (
            "id",
            "plan_unit",
            "target_type",
            "is_master_plan_unit_deleted",
            "is_master_plan_unit_newer",
            "message_label",
        )

    def get_is_master_plan_unit_deleted(self, obj):
        return not obj.plan_unit.is_master_exist

    def get_message_label(self, obj):
        if not obj.plan_unit.is_master_exist:
            return _(
                "Master plan unit has been deleted. Please change or remove the plan unit."
            )
        elif obj.plan_unit.is_master_newer:
            return _("Master plan unit has been updated. Please update the plan unit.")
        return None


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
    targets = PlotSearchTargetSerializer(
        source="plotsearchtarget_set", many=True, read_only=True
    )

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
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchType,
        queryset=PlotSearchType.objects.all(),
        related_serializer=PlotSearchTypeSerializer,
        required=False,
        allow_null=True,
    )
    subtype = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchSubtype,
        queryset=PlotSearchSubtype.objects.all(),
        related_serializer=PlotSearchSubtypeSerializer,
        required=False,
        allow_null=True,
    )
    stage = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchStage,
        queryset=PlotSearchStage.objects.all(),
        related_serializer=PlotSearchStageSerializer,
        required=False,
        allow_null=True,
    )
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

    def update(self, instance, validated_data):
        targets = None
        if "plotsearchtarget_set" in validated_data:
            targets = validated_data.pop("plotsearchtarget_set")
        PlotSearchTarget.objects.filter(plot_search=instance).delete()
        if targets:
            for target in targets:
                d = dict(target)
                PlotSearchTarget.objects.create(
                    plot_search=instance, plan_unit=d["plan_unit"]
                )

        instance = super(PlotSearchUpdateSerializer, self).update(
            instance, validated_data
        )

        return instance

    def validate(self, attrs):
        targets = attrs.get("plotsearchtarget_set")
        if targets:
            for target in targets:
                instance = PlotSearchTarget(**target)
                instance.clean()
        return attrs


class PlotSearchCreateSerializer(PlotSearchUpdateSerializer):
    class Meta:
        model = PlotSearch
        fields = "__all__"

    def create(self, validated_data):
        targets = None
        if "plotsearchtarget_set" in validated_data:
            targets = validated_data.pop("plotsearchtarget_set")

        plot_search = PlotSearch.objects.create(**validated_data)

        if targets:
            for target in targets:
                plot_search_target = PlotSearchTarget.objects.create(
                    plot_search=plot_search,
                    plan_unit=target.get("plan_unit"),
                    target_type=target.get("target_type"),
                )
                plot_search_target.save()

        return plot_search
