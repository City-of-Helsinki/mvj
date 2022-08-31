from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from field_permissions.serializers import FieldPermissionsSerializerMixin
from forms.models import Form
from forms.serializers.form import FormSerializer
from leasing.models import Decision, PlanUnit
from leasing.serializers.decision import DecisionSerializer
from leasing.serializers.land_area import PlanUnitSerializer, PublicPlanUnitSerializer
from leasing.serializers.utils import (
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)
from plotsearch.models import (
    AreaSearch,
    Favourite,
    FavouriteTarget,
    InformationCheck,
    IntendedSubUse,
    IntendedUse,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    TargetInfoLink,
)
from plotsearch.utils import initialize_area_search_form
from users.models import User
from users.serializers import UserSerializer


class PlotSearchSubTypeLinkedSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchSubtype
        fields = (
            "id",
            "name",
            "ordering",
            "show_district",
        )


class PlotSearchTypeLinkedSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchType
        fields = (
            "id",
            "name",
            "ordering",
        )


class PlotSearchSubtypeSerializer(NameModelSerializer):
    plot_search_type = PlotSearchTypeLinkedSerializer()

    class Meta:
        model = PlotSearchSubtype
        fields = (
            "id",
            "name",
            "show_district",
            "target_selection",
            "ordering",
            "plot_search_type",
        )


class IntendedSubUseLinkedSerializer(NameModelSerializer):
    class Meta:
        model = IntendedSubUse
        fields = (
            "id",
            "name",
        )


class IntendedUseLinkedSerializer(NameModelSerializer):
    class Meta:
        model = IntendedUse
        fields = (
            "id",
            "name",
        )


class IntendedSubUseSerializer(NameModelSerializer):
    intended_use = IntendedUseLinkedSerializer()

    class Meta:
        model = IntendedSubUse
        fields = (
            "id",
            "name",
            "intended_use",
        )


class PlotSearchStageSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchStage
        fields = "__all__"


class PlotSearchTargetInfoLinkSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False, required=False, allow_null=True,)

    class Meta:
        model = TargetInfoLink
        fields = (
            "id",
            "url",
            "description",
            "language",
        )


class PlotSearchTargetSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False, allow_null=True)

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
    district = serializers.ReadOnlyField(
        source="plan_unit.lease_area.lease.district.name"
    )
    decisions = DecisionSerializer(
        many=True,
        source="plan_unit.lease_area.lease.decisions",
        required=False,
        allow_null=True,
    )

    master_plan_unit_id = serializers.SerializerMethodField()
    is_master_plan_unit_deleted = serializers.SerializerMethodField()
    is_master_plan_unit_newer = serializers.ReadOnlyField(
        source="plan_unit.is_master_newer"
    )
    message_label = serializers.SerializerMethodField()
    plan_unit = PublicPlanUnitSerializer(read_only=True)
    plan_unit_id = serializers.IntegerField(required=False, allow_null=True)
    info_links = PlotSearchTargetInfoLinkSerializer(many=True, required=False)

    class Meta:
        model = PlotSearchTarget
        fields = (
            "id",
            "plan_unit",
            "plan_unit_id",
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
            "district",
            "info_links",
            "decisions",
        )

    def get_lease_address(self, obj):
        if obj.plan_unit is None:
            return None
        lease_address = (
            obj.plan_unit.lease_area.addresses.all()
            .order_by("-is_primary")
            .values("address")
            .first()
        )
        return lease_address

    def get_master_plan_unit_id(self, obj):
        if obj.plan_unit is None:
            return None
        master = obj.plan_unit.get_master()
        if master:
            return master.id
        return None

    def get_is_master_plan_unit_deleted(self, obj):
        if obj.plan_unit is None:
            return True
        return not obj.plan_unit.master_exists

    def get_message_label(self, obj):
        if obj.plan_unit is None:
            return _("The target has been removed from the system!")
        if not obj.plan_unit.master_exists:
            return _("The target has been removed from the system!")
        elif obj.plan_unit.is_master_newer:
            return _("The target information has changed!")
        return None


class PlotSearchTargetCreateUpdateSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    plan_unit_id = serializers.IntegerField()
    info_links = PlotSearchTargetInfoLinkSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = PlotSearchTarget
        fields = ("id", "plan_unit_id", "target_type", "info_links")

    def create(self, validated_data):
        plan_unit = PlanUnit.objects.get(id=validated_data.pop("plan_unit_id"))
        info_links = validated_data.pop("info_links", [])
        plot_search_target = PlotSearchTarget.objects.create(
            plan_unit=plan_unit, **validated_data
        )

        for info_link in info_links:
            TargetInfoLink.objects.create(
                plot_search_target=plot_search_target, **info_link
            )
        return plot_search_target

    @staticmethod
    def get_prev_links(instance):
        links = TargetInfoLink.objects.filter(plot_search_target=instance)
        return {link.id: link for link in links}

    def update(self, instance, validated_data):
        prev_links = self.get_prev_links(instance)
        for info_link in validated_data.pop("info_links", []):
            try:
                link = TargetInfoLink.objects.get(pk=info_link["id"])
                for k, v in info_link.items():
                    setattr(link, k, v)
                link.save()
                prev_links.pop(info_link["id"])
            except KeyError:
                TargetInfoLink.objects.create(plot_search_target=instance, **info_link)

        # check if any info links are deleted (ie. not found in list) and delete corresponding object
        for k, link in prev_links.items():
            link.delete()

        plan_unit_id = validated_data.pop("plan_unit_id", None)
        if plan_unit_id:
            pu = PlanUnit.objects.get(id=plan_unit_id)
            instance.plan_unit = pu

        return super().update(instance, validated_data)


class PlotSearchTypeSerializer(NameModelSerializer):
    subtypes = PlotSearchSubTypeLinkedSerializer(
        many=True, source="plotsearchsubtype_set"
    )

    class Meta:
        model = PlotSearchType
        fields = ("id", "name", "ordering", "subtypes")


class IntendedUseSerializer(NameModelSerializer):
    subuses = IntendedSubUseLinkedSerializer(many=True, source="intendedsubuse_set")

    class Meta:
        ref_name = "plot_intended_use"
        model = IntendedUse
        fields = ("id", "name", "subuses")


class PlotSearchSerializerBase(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = PlotSearchTypeSerializer(source="subtype.plot_search_type", read_only=True)
    subtype = PlotSearchSubtypeSerializer()
    stage = PlotSearchStageSerializer()

    form = InstanceDictPrimaryKeyRelatedField(
        instance_class=Form,
        queryset=Form.objects.prefetch_related(
            "sections__fields__choices",
            "sections__subsections__fields__choices",
            "sections__subsections__subsections__fields__choices",
            "sections__subsections__subsections__subsections",
        ),
        related_serializer=FormSerializer,
        required=False,
        allow_null=True,
    )

    decisions = InstanceDictPrimaryKeyRelatedField(
        instance_class=Decision,
        queryset=Decision.objects.all(),
        related_serializer=DecisionSerializer,
        required=False,
        allow_null=True,
        many=True,
    )

    class Meta:
        model = PlotSearch
        fields = "__all__"


class PlotSearchRetrieveSerializer(PlotSearchSerializerBase):
    preparers = UserSerializer(many=True)
    plot_search_targets = PlotSearchTargetSerializer(many=True, read_only=True)

    class Meta:
        model = PlotSearch
        fields = (
            "id",
            "type",
            "subtype",
            "stage",
            "search_class",
            "form",
            "decisions",
            "preparers",
            "plot_search_targets",
            "deleted",
            "created_at",
            "modified_at",
            "name",
            "begin_at",
            "end_at",
        )


class PlotSearchUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(required=True)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchType,
        queryset=PlotSearchType.objects.all(),
        required=False,
        allow_null=True,
    )
    subtype = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchSubtype,
        queryset=PlotSearchSubtype.objects.all(),
        related_serializer=PlotSearchSubtypeSerializer,
        required=True,
    )
    stage = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchStage,
        queryset=PlotSearchStage.objects.all(),
        related_serializer=PlotSearchStageSerializer,
        required=True,
    )
    preparers = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=True,
        many=True,
    )
    plot_search_targets = PlotSearchTargetCreateUpdateSerializer(
        many=True, required=False
    )

    class Meta:
        model = PlotSearch
        fields = "__all__"

    def to_representation(self, instance):
        return PlotSearchRetrieveSerializer().to_representation(instance)

    @staticmethod
    def dict_to_instance(dictionary, model):
        if isinstance(dictionary, model):
            return dictionary
        instance, created = model.objects.get_or_create(id=dictionary["id"])
        if created:
            for k, v in dictionary:
                setattr(instance, k, v)
            instance.save()
        return instance

    @staticmethod
    def handle_targets(targets, instance):
        exist_target_ids = []
        for target in targets:
            target_id = target.get("id")
            target["plot_search"] = instance
            if target_id:
                plot_search_target = PlotSearchTarget.objects.get(
                    id=target_id, plot_search=instance
                )

                # Check if target is changed and update
                # This is to avoid calling .clean() -function if no changes to targets are made
                is_updated = False
                for k, v in target.items():
                    if getattr(plot_search_target, k) != v:
                        is_updated = True
                if is_updated:
                    PlotSearchTargetCreateUpdateSerializer().update(
                        plot_search_target, target
                    )
            else:
                plot_search_target = PlotSearchTargetCreateUpdateSerializer().create(
                    target
                )
            exist_target_ids.append(plot_search_target.id)

        PlotSearchTarget.objects.filter(plot_search=instance).exclude(
            id__in=exist_target_ids
        ).delete()

    def update(self, instance, validated_data):

        targets = validated_data.pop("plot_search_targets", None)
        subtype = validated_data.pop("subtype", None)
        stage = validated_data.pop("stage", None)
        preparers = validated_data.pop("preparers", None)

        if subtype:
            validated_data["subtype"] = self.dict_to_instance(
                subtype, PlotSearchSubtype
            )

        if stage:
            validated_data["stage"] = self.dict_to_instance(stage, PlotSearchStage)

        if preparers:
            validated_data["preparers"] = list()
            for preparer in preparers:
                validated_data["preparers"].append(
                    self.dict_to_instance(preparer, User)
                )

        instance = super(PlotSearchUpdateSerializer, self).update(
            instance, validated_data
        )

        if targets is not None:
            self.handle_targets(targets, instance)

        return instance


class PlotSearchCreateSerializer(PlotSearchUpdateSerializer):
    subtype = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchSubtype,
        queryset=PlotSearchSubtype.objects.all(),
        related_serializer=PlotSearchSubtypeSerializer,
        required=False,
    )
    stage = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchStage,
        queryset=PlotSearchStage.objects.all(),
        related_serializer=PlotSearchStageSerializer,
        required=False,
    )
    preparers = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        many=True,
    )

    plot_search_targets = PlotSearchTargetSerializer(many=True, required=False)
    plan_unit = PlanUnitSerializer(read_only=True)

    class Meta:
        model = PlotSearch
        fields = "__all__"

    @staticmethod
    def handle_targets(targets, plot_search):
        for target in targets:
            plan_unit = PlanUnit.objects.get(id=target.get("plan_unit_id"))
            plot_search_target = PlotSearchTarget.objects.create(
                plot_search=plot_search,
                plan_unit=plan_unit,
                target_type=target.get("target_type"),
            )
            plot_search_target.save()
            if "info_links" in target:
                for link in target["info_links"]:
                    link["plot_search_target"] = plot_search_target
                    plot_search_target.info_links.add(
                        PlotSearchTargetInfoLinkSerializer().create(link)
                    )

    def create(self, validated_data):
        targets = None
        if "plot_search_targets" in validated_data:
            targets = validated_data.pop("plot_search_targets")
        decisions = None
        if "decisions" in validated_data:
            decisions = validated_data.pop("decisions")

        plot_search = PlotSearch.objects.create(**validated_data)

        if targets:
            self.handle_targets(targets, plot_search)
        if decisions:
            for decision in decisions:
                plot_search.decisions.add(decision)
            plot_search.save()

        return plot_search


class FavouriteTargetSerializer(serializers.ModelSerializer):
    plot_search_target = InstanceDictPrimaryKeyRelatedField(
        instance_class=PlotSearchTarget,
        queryset=PlotSearchTarget.objects.all(),
        related_serializer=PlotSearchTargetSerializer,
        required=True,
    )
    plot_search = serializers.ReadOnlyField(source="plot_search_target.plot_search.id")

    class Meta:
        model = FavouriteTarget
        fields = ("plot_search_target", "plot_search")


class FavouriteSerializer(serializers.ModelSerializer):
    targets = FavouriteTargetSerializer(many=True)

    class Meta:
        model = Favourite
        fields = ("id", "created_at", "modified_at", "targets")

    @staticmethod
    def handle_targets(targets, favourite):
        FavouriteTarget.objects.filter(favourite=favourite).delete()
        for target in targets:
            FavouriteTarget.objects.create(
                plot_search_target=target.get("plot_search_target"), favourite=favourite
            )

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        targets = None
        if "targets" in validated_data:
            targets = validated_data.pop("targets")

        favourite = Favourite.objects.create(user=user, **validated_data)

        if targets:
            self.handle_targets(targets, favourite)

        return favourite

    def update(self, instance, validated_data):
        targets = None
        if "targets" in validated_data:
            targets = validated_data.pop("targets")
        instance = super().update(instance, validated_data)
        if targets is not None:
            self.handle_targets(targets, instance)
            instance.save()
        return instance


class AreaSearchSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    geometry = GeometryField()

    class Meta:
        model = AreaSearch
        fields = (
            "id",
            "start_date",
            "end_date",
            "geometry",
            "description_area",
            "description_intended_use",
            "intended_use",
        )

    def create(self, validated_data):
        validated_data["form"] = initialize_area_search_form()
        return super().create(validated_data)


class InformationCheckSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(read_only=True)
    mark_all = serializers.BooleanField(write_only=True)
    name = serializers.CharField(read_only=True)

    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
    )
    modified_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = InformationCheck
        fields = (
            "id",
            "name",
            "state",
            "preparer",
            "comment",
            "modified_at",
            "mark_all",
        )
