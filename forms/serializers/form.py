from ast import literal_eval
from collections import OrderedDict

from deepmerge import always_merger
from enumfields.drf.serializers import EnumSerializerField
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework_gis.fields import GeometryField

from leasing.models import Financing, Hitas, Management
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField
from plotsearch.enums import DeclineReason
from plotsearch.models import (
    AreaSearch,
    InformationCheck,
    PlotSearch,
    PlotSearchTarget,
    TargetStatus,
)
from plotsearch.models.plot_search import MeetingMemo, ProposedFinancingManagement
from plotsearch.utils import get_applicant
from users.models import User
from users.serializers import UserSerializer

from ..enums import ApplicantType, FormState
from ..models import Answer, Choice, Entry, Field, Form, Section
from ..models.form import AnswerOpeningRecord, Attachment, EntrySection
from ..validators.answer import (
    ControlShareValidation,
    FieldRegexValidator,
    RequiredFormFieldValidator,
)


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

    def to_internal_value(self, data):
        serializer = self.parent.parent.__class__()
        return serializer.to_internal_value(data)


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = (
            "text",
            "text_fi",
            "text_en",
            "text_sv",
            "value",
            "action",
            "has_text_input",
            "sort_order",
        )


class FieldSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=Field.FIELD_TYPES)
    identifier = serializers.CharField()
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Field
        fields = (
            "id",
            "identifier",
            "type",
            "label",
            "label_en",
            "label_fi",
            "label_sv",
            "hint_text",
            "hint_text_en",
            "hint_text_fi",
            "hint_text_sv",
            "enabled",
            "required",
            "validation",
            "action",
            "sort_order",
            "choices",
            "section_id",
            "default_value",
        )

    def create(self, validated_data):
        fsection = validated_data.pop("section_id")
        choices = validated_data.pop("choices", [])
        c_serializer = ChoiceSerializer()

        for choice in choices:
            c_serializer.create(choice)

        fsection = Section.objects.get(pk=fsection)
        return Field.objects.create(section=fsection, **validated_data)

    def update(self, instance, validated_data):
        choices = validated_data.pop("choices", [])
        prev_choices = Choice.objects.filter(field=instance)
        prev_choices = {c.id: c for c in prev_choices}
        c_serializer = ChoiceSerializer()

        for choice in choices:
            try:
                c = Choice.objects.get(pk=choice["id"])
                c_serializer.update(c, choice)
                prev_choices.pop(choice["id"])
            except KeyError:
                choice["field"] = instance
                c_serializer.create(choice)

        # Check if any choice is deleted
        for k, choice in prev_choices.items():
            choice.delete()

        return super(FieldSerializer, self).update(instance, validated_data)


class SectionSerializer(serializers.ModelSerializer):

    subsections = RecursiveSerializer(many=True, required=False, allow_null=True)
    fields = FieldSerializer(many=True, required=False, allow_null=True)
    id = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.CharField(read_only=True)
    applicant_type = EnumSerializerField(enum=ApplicantType, required=False)

    class Meta:
        model = Section
        fields = (
            "id",
            "identifier",
            "title",
            "title_fi",
            "title_en",
            "title_sv",
            "visible",
            "sort_order",
            "add_new_allowed",
            "show_duplication_check",
            "add_new_text",
            "subsections",
            "fields",
            "form_id",
            "parent_id",
            "applicant_type",
            "type",
        )
        validators = []

    def create(self, validated_data):
        fields = validated_data.pop("fields", [])
        subsections = validated_data.pop("subsections", [])
        section = super().create(validated_data)

        f_ser = FieldSerializer()
        for field in fields:
            field["section_id"] = section.id
            f_ser.create(field)

        s_ser = SectionSerializer()
        for sec in subsections:
            sec["parent_id"] = section.id
            sec["form_id"] = section.form.id
            s_ser.create(sec)
        return section

    @staticmethod
    def update_fields(instance, fields):
        # fields
        prev_fields = Field.objects.filter(section=instance)
        prev_fields = {f.id: f for f in prev_fields}
        f_serializer = FieldSerializer()

        for field in fields:
            try:
                f = Field.objects.get(pk=field["id"])
                f_serializer.update(f, field)
                prev_fields.pop(field["id"])
            except KeyError:
                field["section_id"] = instance.id
                f_serializer.create(field)

        # Check if any field is deleted
        for k, field in prev_fields.items():
            field.delete()

    @staticmethod
    def update_subsections(instance, subsections):
        try:
            prev_s_sections = Section.objects.filter(parent=instance)
            prev_s_sections = {s.id: s for s in prev_s_sections}
        except Section.DoesNotExist:
            prev_s_sections = {}

        s_serializer = SectionSerializer()

        for s_section in subsections:
            try:
                s = Section.objects.get(pk=s_section["id"])
                s_serializer.update(s, s_section)
                prev_s_sections.pop(s_section["id"])
            except KeyError:
                s_section["parent_id"] = instance.id
                s_serializer.create(s_section)

        # Check if any section is deleted
        for k, s_section in prev_s_sections.items():
            s_section.delete()

    def update(self, instance, validated_data):
        subsections = validated_data.pop("subsections", [])
        self.update_subsections(instance, subsections)

        fields = validated_data.pop("fields", [])
        self.update_fields(instance, fields)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class FormSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True)
    state = EnumSerializerField(FormState)
    plot_search_name = serializers.CharField(read_only=True, source="plotsearch.name")
    plot_search_id = serializers.IntegerField(read_only=True, source="plotsearch.id")

    class Meta:
        model = Form
        fields = (
            "id",
            "name",
            "is_template",
            "title",
            "sections",
            "state",
            "plot_search_name",
            "plot_search_id",
        )

    @staticmethod
    def get_sections(instance):
        sections = Section.objects.filter(form=instance, parent=None)
        return {section.id: section for section in sections}

    def to_representation(self, instance):
        data = super(FormSerializer, self).to_representation(instance)
        return self.filter_subsections(data)

    @staticmethod
    def filter_subsections(data):
        sections = []
        for sec in data["sections"]:
            if sec["parent_id"] is None:
                sections.append(sec)
        data["sections"] = sections
        return data

    def update(self, instance, validated_data):
        prev_sections = self.get_sections(instance)
        s_serializer = SectionSerializer()
        for section in validated_data.pop("sections", []):
            try:
                s = Section.objects.get(pk=section["id"])
                s_serializer.update(s, section)
                prev_sections.pop(section["id"])
            except KeyError:
                section["form_id"] = instance.id
                if "parent" not in section:
                    section["parent"] = None
                s_serializer.create(section)

        # Check if any section is deleted
        for k, section in prev_sections.items():
            section.delete()
        return super(FormSerializer, self).update(instance, validated_data)


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ("path", "value", "extra_value")


class InformationCheckAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InformationCheck
        fields = (
            "id",
            "name",
        )


class ProposedFinancingManagementSerializer(serializers.HyperlinkedModelSerializer):
    proposed_financing = serializers.PrimaryKeyRelatedField(
        queryset=Financing.objects.all()
    )
    proposed_management = serializers.PrimaryKeyRelatedField(
        queryset=Management.objects.all()
    )
    hitas = serializers.PrimaryKeyRelatedField(queryset=Hitas.objects.all())

    class Meta:
        model = ProposedFinancingManagement
        fields = (
            "proposed_financing",
            "proposed_management",
            "hitas",
            "target_status_id",
        )


class MeetingMemoSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = MeetingMemo
        fields = (
            "id",
            "user",
            "name",
            "target_status",
            "created_at",
            "meeting_memo",
        )

    def create(self, validated_data):
        memo = MeetingMemo.objects.create(
            name=validated_data["name"],
            target_status=validated_data["target_status"],
            user=self.context["request"].user,
        )
        memo.meeting_memo = validated_data["meeting_memo"]
        memo.save()
        return memo


class TargetStatusUpdateSerializer(serializers.HyperlinkedModelSerializer):
    proposed_managements = ProposedFinancingManagementSerializer(
        many=True, required=False
    )
    meeting_memos = MeetingMemoSerializer(many=True, required=False, read_only=True)
    decline_reason = EnumSerializerField(
        enum=DeclineReason, required=False, allow_null=True
    )

    class Meta:
        model = TargetStatus
        fields = (
            "id",
            "share_of_rental_indicator",
            "share_of_rental_denominator",
            "reserved",
            "added_target_to_applicant",
            "counsel_date",
            "decline_reason",
            "arguments",
            "proposed_managements",
            "meeting_memos",
            "reservation_conditions",
        )

    def update(self, instance, validated_data):
        proposed_managements = validated_data.pop("proposed_managements", [])

        pf_serializer = ProposedFinancingManagementSerializer()

        if proposed_managements:
            ProposedFinancingManagement.objects.filter(
                target_status_id=instance.pk
            ).delete()

        for proposed_management in proposed_managements:
            proposed_management["target_status_id"] = instance.pk
            pf_serializer.create(proposed_management)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        instance.save()
        return instance


class TargetStatusSerializer(TargetStatusUpdateSerializer):
    identifier = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()

    def get_address(self, obj):
        target_address = None

        if obj.plot_search_target.plan_unit is not None:
            target_address = (
                obj.plot_search_target.plan_unit.lease_area.addresses.all()
                .order_by("-is_primary")
                .values("address")
                .first()
            )
        elif obj.plot_search_target.custom_detailed_plan is not None:
            target_address = {
                "address": obj.plot_search_target.custom_detailed_plan.address
            }

        return target_address

    def get_identifier(self, obj):
        if obj.plot_search_target.plan_unit is not None:
            return obj.plot_search_target.plan_unit.identifier
        elif obj.plot_search_target.custom_detailed_plan is not None:
            return obj.plot_search_target.custom_detailed_plan.identifier
        else:
            return None

    def get_geometry(self, obj):
        if obj.plot_search_target.plan_unit is not None:
            return GeometryField().to_representation(
                obj.plot_search_target.plan_unit.geometry
            )
        elif obj.plot_search_target.custom_detailed_plan is not None:
            return GeometryField().to_representation(
                obj.plot_search_target.custom_detailed_plan.lease_area.geometry
            )
        else:
            return None

    class Meta:
        model = TargetStatus
        fields = (
            "id",
            "identifier",
            "share_of_rental_indicator",
            "share_of_rental_denominator",
            "reserved",
            "added_target_to_applicant",
            "counsel_date",
            "decline_reason",
            "arguments",
            "proposed_managements",
            "meeting_memos",
            "reservation_conditions",
            "address",
            "geometry",
            "application_identifier",
        )


class TargetStatusListSerializer(serializers.ModelSerializer):
    target_identifier = serializers.CharField(source="plot_search_target.identifier")
    applicants = serializers.SerializerMethodField()

    class Meta:
        model = TargetStatus
        fields = (
            "application_identifier",
            "target_identifier",
            "applicants",
            "id",
            "answer_id",
        )

    @staticmethod
    def get_applicants(obj):
        applicant_list = list()
        get_applicant(obj.answer, applicant_list)
        return applicant_list


class AnswerOpeningRecordSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    possible_preparers = serializers.SerializerMethodField(read_only=True)
    openers = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        many=True,
    )
    time_stamp = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AnswerOpeningRecord
        fields = ("openers", "note", "answer", "id", "possible_preparers", "time_stamp")

    def create(self, validated_data):
        if "openers" not in validated_data:
            validated_data["openers"] = list()
        if not PlotSearch.objects.filter(
            plot_search_targets__answers=validated_data.get("answer")
        ).first().preparers.filter(
            pk=self.context["request"].user.pk
        ).exists() and not self.context[
            "request"
        ].user.has_perm(
            "forms.add_answeropeningrecord"
        ):
            raise PermissionDenied
        validated_data["openers"].append(self.context["request"].user)
        return super().create(validated_data)

    @staticmethod
    def get_possible_preparers(obj):
        targets_qs = obj.answer.targets.all()
        plotsearch_qs = PlotSearch.objects.filter(plot_search_targets__in=targets_qs)

        preparers_list = list()

        for plotsearch in plotsearch_qs:
            for preparer in plotsearch.preparers.all():
                preparers_list.append(preparer)

        return UserSerializer(many=True).to_representation(preparers_list)


class AnswerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    entries = serializers.JSONField(write_only=True)
    entries_data = serializers.DictField(
        read_only=True, child=serializers.CharField(), source="entry_sections"
    )
    targets = InstanceDictPrimaryKeyRelatedField(
        many=True, queryset=PlotSearchTarget.objects.all(), required=False
    )
    target_statuses = TargetStatusSerializer(
        many=True, source="statuses", required=False
    )
    attachments = serializers.ListSerializer(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    area_search = InstanceDictPrimaryKeyRelatedField(
        queryset=AreaSearch.objects.all(), required=False
    )
    information_checks = serializers.SerializerMethodField(read_only=True)
    opening_record = AnswerOpeningRecordSerializer(required=False)
    plot_search_opening_time_stamp = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = (
            "id",
            "form",
            "targets",
            "target_statuses",
            "entries",
            "entries_data",
            "information_checks",
            "attachments",
            "ready",
            "area_search",
            "opening_record",
            "plot_search_opening_time_stamp",
        )
        validators = [
            RequiredFormFieldValidator(),
            FieldRegexValidator(
                "^[0-9]{6}[+AaBbCcDdEeFfYyXxWwVvUu-][0-9]{3}[A-z0-9]$",
                "invalid_ssn",
                "henkilotunnus",
            ),
            FieldRegexValidator(
                "[0-9]{6,7}-?[0-9]{1}$", "invalid_company_id", "y-tunnus"
            ),
            ControlShareValidation(),
        ]

    def get_information_checks(self, obj):
        entry_sections = obj.entry_sections.filter(
            identifier__startswith="hakijan-tiedot["
        )
        information_checks = list(dict())
        for entry_section in entry_sections:
            for information_check in entry_section.informationcheck_set.all():
                if information_check.preparer is not None:
                    preparer = {
                        "id": information_check.preparer.id,
                        "username": information_check.preparer.username,
                        "first_name": information_check.preparer.first_name,
                        "last_name": information_check.preparer.last_name,
                        "is_staff": information_check.preparer.is_staff,
                    }
                else:
                    preparer = None
                information_checks.append(
                    {
                        "id": information_check.id,
                        "name": information_check.name,
                        "preparer": preparer,
                        "state": information_check.state,
                        "comment": information_check.comment,
                        "entry": information_check.entry_section.identifier,
                        "modified_at": information_check.modified_at,
                    }
                )
        return information_checks

    def entry_generator(
        self, entries, path="", sections=None, fields=None, metadata={}
    ):
        if "metadata" in entries:
            metadata.update(entries["metadata"])
        if "sections" in entries:
            yield from self.entry_generator(
                entries["sections"],
                sections=[entry for entry in entries["sections"]],
                metadata=metadata,
                path=path,
            )
        if "fields" in entries:
            yield from self.entry_generator(
                entries["fields"],
                sections=sections,
                fields=[entry for entry in entries["fields"]],
                metadata=metadata,
                path=path,
            )

        if isinstance(entries, list):
            for i, entry in enumerate(entries):
                yield from self.entry_generator(
                    entry,
                    sections=sections,
                    fields=fields,
                    metadata=metadata,
                    path="{}[{}]".format(path, str(i)),
                )
        if isinstance(sections, list):
            for section in sections:
                yield from self.entry_generator(
                    entries[section],
                    sections=section,
                    metadata=metadata,
                    path="{}.{}".format(path, section),
                )
        if not isinstance(fields, list):
            return

        for field in fields:
            value_dict = entries[field]

            # first character is a dot
            yield field, sections, value_dict, metadata, path[1:]

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            check_for_none = (
                attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            )
            if check_for_none is None:
                ret[field.field_name] = None
            elif field.label == "Entries data":
                ret[field.field_name] = self.create_entry(attribute)
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret

    @staticmethod
    def create_entry(attribute):
        entries_dict = dict()
        for entry_section in attribute.all():
            for entry in entry_section.entries.all():
                path_parts = entry.path.split(sep=".")
                try:
                    entry_value = literal_eval(entry.value)
                except (SyntaxError, ValueError):
                    entry_value = entry.value
                value_set = False
                help_dict = dict()
                for part in reversed(path_parts):
                    new_dict = {}
                    if value_set:
                        new_dict[part] = help_dict
                        if part == path_parts[0]:
                            new_dict[part]["metadata"] = entry.entry_section.metadata
                        help_dict = new_dict
                        continue

                    help_dict[part] = {
                        "fields": {
                            entry.field.identifier: {
                                "value": entry_value,
                                "extra_value": entry.extra_value,
                            }
                        }
                    }
                    value_set = True
                    if part == path_parts[0]:
                        help_dict[part]["metadata"] = entry.entry_section.metadata

                always_merger.merge(entries_dict, help_dict)
        return entries_dict

    @staticmethod
    def get_entry_section(
        answer,
        metadata,
        path,
    ):
        entry_section, unused = EntrySection.objects.get_or_create(
            identifier=path.split(".")[0],
            answer=answer,
            defaults={"metadata": metadata},
        )
        return entry_section

    @staticmethod
    def get_field(field_identifier, section_identifier, validated_data):
        try:
            field = Field.objects.get(
                identifier=field_identifier,
                section__identifier=section_identifier,
                section__form=validated_data.get("form"),
            )
        except Field.DoesNotExist:
            raise ValueError
        return field

    def create(self, validated_data):
        entries_data = validated_data.pop("entries")
        targets = validated_data.pop("targets", [])
        attachments = validated_data.pop("attachments", [])
        area_search = validated_data.pop("area_search", None)
        user = self.context["request"].user
        answer = Answer.objects.create(user=user, **validated_data)
        for target in targets:
            answer.targets.add(target)

        for (
            field_identifier,
            section_identifier,
            value,
            metadata,
            path,
        ) in self.entry_generator(entries_data):
            field = self.get_field(field_identifier, section_identifier, validated_data)

            if field.type == "uploadfiles":
                Attachment.objects.filter(id__in=value["value"]).update(path=path)

            entry_section = self.get_entry_section(
                answer,
                metadata,
                path,
            )
            Entry.objects.create(
                entry_section=entry_section,
                field=field,
                value=value["value"],
                extra_value=value["extraValue"],
                path=path,
            )
        for attachent_id in attachments:
            Attachment.objects.filter(id=attachent_id).update(answer=answer)

        if area_search is not None:
            AreaSearch.objects.filter(id=area_search.id).update(answer=answer.pk)
        return answer

    def update(self, instance, validated_data):
        entries_data = validated_data.pop("entries", [])
        Attachment.objects.filter(answer=instance).update(path=None)
        for (
            field_identifier,
            section_identifier,
            value,
            metadata,
            path,
        ) in self.entry_generator(entries_data):
            field = self.get_field(field_identifier, section_identifier, validated_data)

            if field.type == "uploadfiles":
                Attachment.objects.filter(id__in=value["value"]).update(path=path)

            entry_section = self.get_entry_section(
                instance,
                metadata,
                path,
            )
            Entry.objects.update_or_create(
                entry_section=entry_section,
                field=field,
                defaults={"value": value["value"], "extra_value": value["extraValue"]},
                path=path,
            )

        Attachment.objects.filter(answer=instance, path__isnull=True).delete()

        instance.ready = validated_data.get("ready", instance.ready)
        instance.user = self.context["request"].user
        instance.save()
        return instance

    @staticmethod
    def get_plot_search_opening_time_stamp(obj):
        if not hasattr(obj.form, "plotsearch"):
            return
        plotsearch = obj.form.plotsearch
        pst_qs = plotsearch.plot_search_targets.all()
        opening_record = (
            AnswerOpeningRecord.objects.filter(answer__targets__in=pst_qs)
            .order_by("time_stamp")
            .first()
        )
        return opening_record.time_stamp if opening_record is not None else "-"


class AnswerPublicSerializer(AnswerSerializer):
    def create(self, validated_data):
        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        del rep["information_checks"]  # Information checks are not needed in public API
        return rep


class AnswerListSerializer(serializers.ModelSerializer):
    applicants = serializers.SerializerMethodField()
    targets = TargetStatusSerializer(many=True, source="statuses")
    plot_search = serializers.SerializerMethodField()
    plot_search_id = serializers.SerializerMethodField()
    plot_search_type = serializers.SerializerMethodField()
    plot_search_subtype = serializers.SerializerMethodField()
    opening_record = serializers.BooleanField(read_only=False)
    plot_search_end_date = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = (
            "id",
            "plot_search",
            "plot_search_id",
            "plot_search_type",
            "plot_search_subtype",
            "applicants",
            "targets",
            "opening_record",
            "plot_search_end_date",
        )

    @staticmethod
    def get_applicants(obj):
        applicant_list = list()
        get_applicant(obj, applicant_list)
        return applicant_list

    def get_plot_search(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search = obj.form.plotsearch
        return plot_search.name

    def get_plot_search_id(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search = obj.form.plotsearch
        return plot_search.id

    def get_plot_search_type(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search_type = obj.form.plotsearch.subtype.plot_search_type
        return plot_search_type.name

    def get_plot_search_subtype(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search_subtype = obj.form.plotsearch.subtype
        return {
            "name": plot_search_subtype.name,
            "id": plot_search_subtype.id,
            "require_opening_record": plot_search_subtype.require_opening_record,
        }

    @staticmethod
    def get_plot_search_end_date(obj):
        form = obj.form
        if form is None or not hasattr(form, "plotsearch"):
            return None
        return form.plotsearch.end_at.isoformat()


class AttachmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Attachment
        fields = (
            "id",
            "name",
            "attachment",
            "created_at",
            "answer",
            "field",
            "path",
        )

    def save(self, **kwargs):
        kwargs["user"] = self.context["request"].user
        return super().save(**kwargs)


class ReadAttachmentSerializer(AttachmentSerializer):
    field = serializers.CharField(source="field.identifier")
