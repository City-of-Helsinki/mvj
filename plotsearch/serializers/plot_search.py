import requests
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from pyproj import Proj, transform
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_gis.fields import GeometryField

from field_permissions.serializers import FieldPermissionsSerializerMixin
from forms.management.commands.generate_areasearch_form import (
    initialize_area_search_form,
)
from forms.models import Answer, Form
from forms.models.form import AnswerOpeningRecord
from forms.serializers.form import AnswerSerializer, FormSerializer
from leasing.models import Decision, PlanUnit, Plot
from leasing.models.land_area import CustomDetailedPlan
from leasing.serializers.decision import DecisionSerializer
from leasing.serializers.land_area import (
    CustomDetailedPlanSerializer,
    PlanUnitSerializer,
    PublicPlanUnitSerializer,
)
from leasing.serializers.lease import DistrictSerializer
from leasing.serializers.utils import (
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)
from plotsearch.enums import RelatedPlotApplicationContentType
from plotsearch.models import (
    AreaSearch,
    AreaSearchIntendedUse,
    Favourite,
    FavouriteTarget,
    InformationCheck,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    RelatedPlotApplication,
)
from plotsearch.models.info_links import TargetInfoLink
from plotsearch.models.plot_search import (
    FAQ,
    AreaSearchAttachment,
    AreaSearchStatus,
    AreaSearchStatusNote,
    DirectReservationLink,
)
from plotsearch.serializers.info_links import PlotSearchTargetInfoLinkSerializer
from plotsearch.utils import (
    compose_direct_reservation_mail_body,
    compose_direct_reservation_mail_subject,
    get_applicant,
    map_intended_use_to_lessor,
    pop_default,
)
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
            "require_opening_record",
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
            "require_opening_record",
        )


class IntendedUseLinkedSerializer(NameModelSerializer):
    class Meta:
        model = AreaSearchIntendedUse
        fields = (
            "id",
            "name",
        )


class PlotSearchStageSerializer(NameModelSerializer):
    class Meta:
        model = PlotSearchStage
        fields = ("id", "name", "stage")


class PlotSearchTargetSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    # TODO clean up SerializerMethodFields. It will need work in user interface also
    id = serializers.IntegerField(required=False, allow_null=True)

    lease_id = serializers.SerializerMethodField()
    lease_identifier = serializers.SerializerMethodField()
    lease_hitas = serializers.SerializerMethodField()
    lease_address = serializers.SerializerMethodField()
    lease_financing = serializers.SerializerMethodField()
    lease_management = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    municipality_id = serializers.SerializerMethodField()
    lease_type = serializers.SerializerMethodField()
    lease_state = serializers.SerializerMethodField()
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
    custom_detailed_plan = CustomDetailedPlanSerializer(read_only=True)
    custom_detailed_plan_id = serializers.IntegerField(required=False, allow_null=True)
    reservation_recipients = serializers.SerializerMethodField()
    reservation_readable_identifier = serializers.CharField(
        read_only=True,
        required=False,
        source="reservation_identifier.identifier.identifier",
    )

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
            "lease_id",
            "lease_identifier",
            "lease_hitas",
            "lease_address",
            "lease_financing",
            "lease_management",
            "district",
            "municipality_id",
            "lease_type",
            "lease_state",
            "info_links",
            "decisions",
            "custom_detailed_plan",
            "custom_detailed_plan_id",
            "reservation_recipients",
            "reservation_identifier",
            "reservation_readable_identifier",
        )

    @staticmethod
    def _get_plan_unit_or_custom_detailed_plan(obj):
        if obj.plan_unit is not None:
            return obj.plan_unit
        elif obj.custom_detailed_plan is not None:
            return obj.custom_detailed_plan
        else:
            return None

    def get_lease_id(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        return target.lease_area.lease.id

    def get_lease_identifier(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        return target.lease_area.lease.identifier.identifier

    def get_lease_hitas(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None or target.lease_area.lease.hitas is None:
            return None
        return target.lease_area.lease.hitas.name

    def get_lease_address(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        lease_address = (
            target.lease_area.addresses.all()
            .order_by("-is_primary")
            .values("address")
            .first()
        )
        return lease_address

    def get_lease_financing(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None or target.lease_area.lease.financing is None:
            return None
        return target.lease_area.lease.financing.name

    def get_lease_management(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None or target.lease_area.lease.management is None:
            return None
        return target.lease_area.lease.management.name

    def get_district(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        return DistrictSerializer().to_representation(target.lease_area.lease.district)

    def get_municipality_id(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        return target.lease_area.lease.municipality.id

    def get_lease_type(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None:
            return None
        return target.lease_area.lease.type.id

    def get_lease_state(self, obj):
        target = self._get_plan_unit_or_custom_detailed_plan(obj)
        if target is None or target.lease_area.lease.state is None:
            return None
        return target.lease_area.lease.state.value

    def get_master_plan_unit_id(self, obj):
        if obj.plan_unit is None:
            return None
        master = obj.plan_unit.get_master()
        if master:
            return master.id
        return None

    def get_is_master_plan_unit_deleted(self, obj):
        if obj.custom_detailed_plan is not None:
            return False
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

    def get_reservation_recipients(self, instance):
        target_statuses = instance.statuses.filter(reserved=True)
        reservation_recipients_with_share = list()
        for target_status in target_statuses:
            reservation_recipients = list()
            get_applicant(target_status.answer, reservation_recipients)
            reservation_recipients_with_share.append(
                {
                    "reservation_recipients": reservation_recipients,
                    "share_of_rental": "{}/{}".format(
                        target_status.share_of_rental_indicator,
                        target_status.share_of_rental_denominator,
                    ),
                    "target_status_id": target_status.id,
                }
            )
        return reservation_recipients_with_share


class PlotSearchTargetCreateUpdateSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    plan_unit_id = serializers.IntegerField(required=False, allow_null=True)
    info_links = PlotSearchTargetInfoLinkSerializer(
        many=True, required=False, allow_null=True
    )
    custom_detailed_plan_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = PlotSearchTarget
        fields = (
            "id",
            "plan_unit_id",
            "custom_detailed_plan_id",
            "target_type",
            "info_links",
            "reservation_identifier",
        )

    def create(self, validated_data):
        custom_detailed_plan, plan_unit = self.get_plan_unit_or_custom_detailed_plan(
            validated_data
        )

        info_links = validated_data.pop("info_links", [])
        if plan_unit is not None:
            plot_search_target = PlotSearchTarget.objects.create(
                plan_unit=plan_unit, **validated_data
            )
        else:
            plot_search_target = PlotSearchTarget.objects.create(
                custom_detailed_plan=custom_detailed_plan, **validated_data
            )

        for info_link in info_links:
            TargetInfoLink.objects.create(
                plot_search_target=plot_search_target, **info_link
            )
        return plot_search_target

    def get_plan_unit_or_custom_detailed_plan(self, validated_data):
        try:
            plan_unit = PlanUnit.objects.get(id=validated_data.get("plan_unit_id"))
        except PlanUnit.DoesNotExist:
            plan_unit = None
        try:
            custom_detailed_plan = CustomDetailedPlan.objects.get(
                id=validated_data.get("custom_detailed_plan_id")
            )
        except CustomDetailedPlan.DoesNotExist:
            custom_detailed_plan = None
        if (plan_unit is None and custom_detailed_plan is None) or (
            plan_unit is not None and custom_detailed_plan is not None
        ):
            raise BadRequest
        return custom_detailed_plan, plan_unit

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

        instance.plan_unit = None
        instance.custom_detailed_plan = None

        custom_detailed_plan, plan_unit = self.get_plan_unit_or_custom_detailed_plan(
            validated_data
        )

        if plan_unit is not None:
            instance.plan_unit = plan_unit
        if custom_detailed_plan is not None:
            instance.custom_detailed_plan = custom_detailed_plan

        return super().update(instance, validated_data)


class PlotSearchTypeSerializer(NameModelSerializer):
    subtypes = PlotSearchSubTypeLinkedSerializer(
        many=True, source="plotsearchsubtype_set"
    )

    class Meta:
        model = PlotSearchType
        fields = ("id", "name", "ordering", "subtypes")


class IntendedUseSerializer(NameModelSerializer):
    class Meta:
        ref_name = "plot_intended_use"
        model = AreaSearchIntendedUse
        fields = ("id", "name")


class IntendedUsePlotsearchPublicSerializer(NameModelSerializer):
    class Meta:
        ref_name = "plot_intended_use_public"
        model = AreaSearchIntendedUse
        fields = ("id", "name")


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

    opening_record = serializers.SerializerMethodField()

    class Meta:
        model = PlotSearch
        fields = ("__all__", "opening_record")

    @staticmethod
    def get_opening_record(instance):
        pst_qs = instance.plot_search_targets.all()
        opening_record = (
            AnswerOpeningRecord.objects.filter(answer__targets__in=pst_qs)
            .order_by("time_stamp")
            .first()
        )
        return opening_record.time_stamp if opening_record is not None else "-"

    @staticmethod
    def get_answers_count(instance):
        pst_qs = instance.plot_search_targets.all()
        opening_record_count = (
            Answer.objects.filter(targets__in=pst_qs)
            .exclude(opening_record__isnull=False)
            .count()
        )
        return opening_record_count


class PlotSearchRetrieveSerializer(PlotSearchSerializerBase):
    preparers = UserSerializer(many=True)
    plot_search_targets = PlotSearchTargetSerializer(many=True, read_only=True)
    opening_record = serializers.SerializerMethodField()

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
            "opening_record",
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


class PlotSearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotSearch
        fields = (
            "id",
            "name",
        )


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


class AreaSearchAttachmentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = AreaSearchAttachment
        fields = (
            "id",
            "user",
            "name",
            "area_search",
            "created_at",
            "attachment",
        )

    def create(self, validated_data):
        attachment = AreaSearchAttachment.objects.create(
            name=validated_data["name"],
            area_search=validated_data.pop("area_search", None),
            user=self.context["request"].user,
        )
        attachment.attachment = validated_data["attachment"]
        attachment.save()
        return attachment


class AreaSearchStatusNoteSerializer(serializers.ModelSerializer):
    preparer = UserSerializer(read_only=True)
    time_stamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AreaSearchStatusNote
        fields = (
            "preparer",
            "note",
            "time_stamp",
        )


class AreaSearchStatusSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    status_notes = AreaSearchStatusNoteSerializer(required=False, many=True)

    class Meta:
        model = AreaSearchStatus
        fields = (
            "decline_reason",
            "status_notes",
            "preparer_note",
        )

    def create_area_status_note(self, instance, status_note):
        if isinstance(status_note, list) and len(status_note) != 0:
            note = status_note[0].get("note", None)
            if note is not None:
                AreaSearchStatusNote.objects.create(
                    preparer=self.context["request"].user,
                    note=note,
                    time_stamp=timezone.now(),
                    area_search_status=instance,
                )

    def create(self, validated_data):
        status_note = validated_data.pop("status_notes", None)
        instance = super().create(validated_data)
        self.create_area_status_note(instance, status_note)
        return instance

    def update(self, instance, validated_data):
        status_note = validated_data.pop("status_notes", None)
        instance = super().update(instance, validated_data)
        self.create_area_status_note(instance, status_note)
        return instance


class AreaSearchSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
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
    applicants = serializers.SerializerMethodField()
    geometry = GeometryField()

    area_search_attachments = InstanceDictPrimaryKeyRelatedField(
        instance_class=AreaSearchAttachment,
        queryset=AreaSearchAttachment.objects.all(),
        related_serializer=AreaSearchAttachmentSerializer,
        required=False,
        allow_null=True,
        many=True,
    )

    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
    )
    area_search_status = AreaSearchStatusSerializer(required=False, allow_null=True)

    class Meta:
        model = AreaSearch
        fields = (
            "id",
            "form",
            "applicants",
            "start_date",
            "end_date",
            "geometry",
            "description_area",
            "description_intended_use",
            "intended_use",
            "area_search_attachments",
            "address",
            "district",
            "preparer",
            "lessor",
            "identifier",
            "state",
            "received_date",
            "area_search_status",
        )

    def create(self, validated_data):
        area_form_qs = Form.objects.filter(is_area_form=True)
        area_search_status = validated_data.pop("area_search_status", None)
        # When areasearch form does not exist it will be initialized
        if area_form_qs.exists():
            validated_data["form"] = area_form_qs.last()
        else:
            validated_data["form"] = initialize_area_search_form()
        attachments = validated_data.pop("area_search_attachments", [])

        inproj = Proj(init="epsg:4326")
        outproj = Proj(init="epsg:3879")
        multipolygon = list()

        for x1, y1 in validated_data["geometry"].coords[0][0]:
            multipolygon.append(transform(inproj, outproj, x1, y1))

        multipolygon_str = ",".join(["{} {}".format(y1, x1) for x1, y1 in multipolygon])

        url = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"
        params = {
            "service": "wfs",
            "version": "2.0.0",
            "request": "getFeature",
            "typeName": "avoindata:Osoiteluettelo_piste_rekisteritiedot",
            "srsName": "EPSG:4326",
            "outputFormat": "application/json",
            "cql_filter": "intersects(geom,MULTIPOLYGON((({}))))".format(
                multipolygon_str
            ),
        }
        response = requests.get(url, params=params)

        results = response.json()
        if results["numberReturned"] == 0:
            params.update({"typeName": "avoindata:Kaupunginosajako"})

            response = requests.get(url, params=params)

            results = response.json()

        validated_data["address"] = results["features"][0]["properties"].get(
            "katuosoite", None
        )
        validated_data["district"] = results["features"][0]["properties"].get(
            "kaupunginosa_nimi_fi", None
        )

        if validated_data["district"] is None:
            validated_data["district"] = results["features"][0]["properties"].get(
                "nimi_fi", None
            )

        area_search = AreaSearch.objects.create(**validated_data)
        area_search.lessor = map_intended_use_to_lessor(
            validated_data.pop("intended_use", None)
        )
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            area_search.user = request.user
        area_search.save()
        for attachment in attachments:
            attachment.area_search = area_search
            attachment.save()

        as_serializer = AreaSearchStatusSerializer(
            data=area_search_status, context=self.context
        )
        if as_serializer.is_valid():
            as_serializer.save()

        return area_search

    @staticmethod
    def get_applicants(obj):
        applicant_list = list()
        if obj.answer is not None:
            get_applicant(obj.answer, applicant_list)
        return applicant_list

    def update(self, instance, validated_data):
        area_search_status = validated_data.pop("area_search_status", None)
        instance = super().update(instance, validated_data)
        area_search_status_qs = AreaSearchStatus.objects.filter(area_search=instance)
        as_serializer = AreaSearchStatusSerializer(context=self.context)

        if area_search_status_qs.exists():
            area_search_status = as_serializer.update(
                area_search_status_qs.get(), area_search_status
            )
        elif area_search_status:
            area_search_status = as_serializer.create(area_search_status)

        instance.area_search_status = area_search_status
        instance.save()

        return instance


class AreaSearchDetailSerializer(AreaSearchSerializer):
    answer = AnswerSerializer(read_only=True, required=False)
    plot = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = AreaSearch
        fields = (
            "id",
            "form",
            "applicants",
            "start_date",
            "end_date",
            "geometry",
            "description_area",
            "description_intended_use",
            "intended_use",
            "area_search_attachments",
            "address",
            "district",
            "preparer",
            "lessor",
            "identifier",
            "state",
            "received_date",
            "area_search_status",
            "answer",
            "plot",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        plot_identifiers = (
            Plot.objects.filter(geometry__intersects=instance.geometry)
            .values("identifier")
            .distinct("identifier")
        )
        identifiers = list()
        if plot_identifiers.exists():
            for plot_identifier in plot_identifiers:
                identifiers.append(plot_identifier["identifier"])
            ret.update({"plot": identifiers})
        else:
            ret.update({"plot": None})
        return ret


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


class DirectReservationLinkSerializer(serializers.ModelSerializer):
    uuid = serializers.ReadOnlyField()
    url = serializers.SerializerMethodField()
    targets = InstanceDictPrimaryKeyRelatedField(
        queryset=PlotSearchTarget.objects.all(), many=True
    )
    lang_choices = ("FI", "SE", "EN")
    language = serializers.ChoiceField(lang_choices, allow_blank=True, required=False)
    first_name = serializers.CharField(allow_blank=True, required=False)
    last_name = serializers.CharField(allow_blank=True, required=False)
    email = serializers.CharField(allow_blank=True, required=False)
    company = serializers.CharField(allow_blank=True, required=False)
    covering_note = serializers.CharField(allow_blank=True, required=False)
    send_copy = serializers.BooleanField(required=False)
    send_mail = serializers.BooleanField(required=False)

    class Meta:
        model = DirectReservationLink
        fields = (
            "uuid",
            "url",
            "targets",
            "language",
            "first_name",
            "last_name",
            "email",
            "company",
            "covering_note",
            "send_copy",
            "send_mail",
        )

    def get_url(self, obj):
        return obj.get_external_url()

    def create(self, validated_data):
        language = pop_default(validated_data, "language", "en")
        first_name = pop_default(validated_data, "first_name", "")
        last_name = pop_default(validated_data, "last_name", "")
        email = pop_default(validated_data, "email", None)
        company = pop_default(validated_data, "company", None)
        covering_note = pop_default(validated_data, "covering_note", "")
        send_copy = pop_default(validated_data, "send_copy", False)
        send_email = pop_default(validated_data, "send_mail", False)

        instance = super().create(validated_data)

        if send_email and email:
            receivers = [email]

            if send_copy:
                user = None
                request = self.context.get("request")
                if request and hasattr(request, "user"):
                    user = request.user
                receivers.append(user.email)

            send_mail(
                compose_direct_reservation_mail_subject(language),
                compose_direct_reservation_mail_body(
                    first_name,
                    last_name,
                    company,
                    instance.get_external_url(),
                    covering_note,
                    language,
                ),
                None,
                receivers,
                False,
            )

        return instance


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = (
            "question",
            "answer",
        )


class RelatedPlotApplicationCreateDeleteSerializer(serializers.ModelSerializer):
    content_type_model = serializers.ChoiceField(
        write_only=True, choices=RelatedPlotApplicationContentType.choices()
    )

    class Meta:
        model = RelatedPlotApplication
        fields = (
            "id",
            "lease",
            "content_type",
            "content_type_model",
            "object_id",
        )
        read_only_fields = ("id", "content_type")

    def validate(self, data):
        super().validate(data)
        content_type_model = data.get("content_type_model")
        object_id = data.get("object_id")
        content_type = ContentType.objects.get(
            model=content_type_model, app_label="plotsearch"
        )
        try:
            content_type.model_class().objects.get(pk=object_id)
        except ObjectDoesNotExist:
            raise ValidationError(
                "Related object not found with object_id and content_type_model"
            )
        return data

    def create(self, validated_data):
        content_type_model = validated_data.pop("content_type_model")
        content_type = ContentType.objects.get(
            model=content_type_model, app_label="plotsearch"
        )
        related_plot_application = RelatedPlotApplication.objects.create(
            content_type=content_type, **validated_data
        )
        return related_plot_application
