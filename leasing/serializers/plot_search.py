from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import (
    PlanUnit,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
)
from leasing.serializers.land_area import PlanUnitSerializer
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

    lease_identifier = serializers.ReadOnlyField(
        source="plan_unit.lease_area.lease.identifier.identifier"
    )
    lease_hitas = serializers.ReadOnlyField(
        source="plan_unit.lease_area.lease.hitas.name"
    )
    lease_address = serializers.SerializerMethodField()
    lease_financing = serializers.ReadOnlyField(
        source="plan_unit.lease_area.lease.financing.name"
    )
    lease_management = serializers.ReadOnlyField(
        source="plan_unit.lease_area.lease.management.name"
    )

    master_plan_unit_id = serializers.SerializerMethodField()
    is_master_plan_unit_deleted = serializers.SerializerMethodField()
    is_master_plan_unit_newer = serializers.ReadOnlyField(
        source="plan_unit.is_master_newer"
    )
    message_label = serializers.SerializerMethodField()
    plan_unit = PlanUnitSerializer(read_only=True)

    class Meta:
        model = PlotSearchTarget
        fields = (
            "id",
            "plan_unit",
            "target_type",
            "master_plan_unit_id",
            "is_master_plan_unit_deleted",
            "is_master_plan_unit_newer",
            "message_label",
            "lease_identifier",
            "lease_hitas",
            "lease_address",
            "lease_financing",
            "lease_management",
        )

    def get_lease_address(self, obj):
        lease_address = (
            obj.plan_unit.lease_area.addresses.all()
            .order_by("-is_primary")
            .values("address")
            .first()
        )
        return lease_address

    def get_master_plan_unit_id(self, obj):
        master = obj.plan_unit.get_master()
        if master:
            return master.id
        return None

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


class PlotSearchTargetCreateUpdateSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    plan_unit = PlanUnitSerializer(read_only=True)
    plan_unit_id = serializers.IntegerField()

    class Meta:
        model = PlotSearchTarget
        fields = (
            "id",
            "plan_unit",
            "plan_unit_id",
            "target_type",
        )


class PlotSearchTypeSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchType
        fields = "__all__"


class PlotSearchSerializerBase(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer(source="subtype.plot_search_type", read_only=True)
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchListSerializer(PlotSearchSerializerBase):
    pass


class PlotSearchRetrieveSerializer(PlotSearchSerializerBase):
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
    type = serializers.PrimaryKeyRelatedField(
        queryset=PlotSearchType.objects.all(), required=False
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
    targets = PlotSearchTargetCreateUpdateSerializer(
        source="plotsearchtarget_set", many=True, required=False
    )

    class Meta:
        model = PlotSearch
        fields = "__all__"

    def update(self, instance, validated_data):
        targets = None
        if "plotsearchtarget_set" in validated_data:
            targets = validated_data.pop("plotsearchtarget_set")

        exist_target_ids = []
        if targets:
            for target in targets:
                target_type = target.get("target_type")

                target_id = target.get("id")
                if target_id:
                    plot_search_target = PlotSearchTarget.objects.get(
                        id=target_id, plot_search=instance
                    )
                    plot_search_target.target_type = target_type
                    plot_search_target.save()
                else:
                    plan_unit_id = target.get("plan_unit_id")
                    plan_unit = PlanUnit.objects.get(id=plan_unit_id)
                    plot_search_target = PlotSearchTarget.objects.create(
                        plot_search=instance,
                        plan_unit=plan_unit,
                        target_type=target_type,
                    )

                exist_target_ids.append(plot_search_target.id)
        PlotSearchTarget.objects.filter(plot_search=instance).exclude(
            id__in=exist_target_ids
        ).delete()

        instance = super(PlotSearchUpdateSerializer, self).update(
            instance, validated_data
        )

        return instance


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
                plan_unit = PlanUnit.objects.get(id=target.get("plan_unit_id"))
                plot_search_target = PlotSearchTarget.objects.create(
                    plot_search=plot_search,
                    plan_unit=plan_unit,
                    target_type=target.get("target_type"),
                )
                plot_search_target.save()

        return plot_search
