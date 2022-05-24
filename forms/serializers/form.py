from ast import literal_eval
from collections import OrderedDict

from deepmerge import always_merger
from enumfields.drf.serializers import EnumSerializerField
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework_gis.fields import GeometryField

from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField
from plotsearch.models import ApplicationStatus, PlotSearchTarget

from ..enums import FormState
from ..models import Answer, Choice, Entry, Field, FieldType, Form, Section
from ..models.form import Attachment, EntrySection
from ..validators.answer import FieldRegexValidator, RequiredFormFieldValidator


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
        fields = ("text", "value", "action", "has_text_input")


class FieldSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.PrimaryKeyRelatedField(queryset=FieldType.objects.all())
    identifier = serializers.ReadOnlyField(read_only=True)
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Field
        fields = (
            "id",
            "identifier",
            "type",
            "label",
            "hint_text",
            "enabled",
            "required",
            "validation",
            "action",
            "sort_order",
            "choices",
            "section_id",
        )

    def create(self, validated_data):
        fsection = validated_data.pop("section_id")
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
    identifier = serializers.ReadOnlyField(read_only=True)
    type = serializers.CharField(read_only=True)

    class Meta:
        model = Section
        fields = (
            "id",
            "identifier",
            "title",
            "visible",
            "sort_order",
            "add_new_allowed",
            "add_new_text",
            "subsections",
            "fields",
            "form_id",
            "parent_id",
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

    class Meta:
        model = Form
        fields = ("id", "name", "is_template", "title", "sections", "state")

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


class AnswerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    entries = serializers.JSONField(write_only=True)
    entries_data = serializers.DictField(
        read_only=True, child=serializers.CharField(), source="entry_sections"
    )
    targets = InstanceDictPrimaryKeyRelatedField(
        many=True, queryset=PlotSearchTarget.objects.all()
    )
    attachments = serializers.ListSerializer(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Answer
        fields = (
            "id",
            "form",
            "targets",
            "entries",
            "entries_data",
            "attachments",
            "ready",
        )
        validators = [
            RequiredFormFieldValidator(),
            FieldRegexValidator(
                "^[0-9]{6}[+Aa-][0-9]{3}[A-z0-9]$", "invalid_ssn", "henkilotunnus"
            ),
            FieldRegexValidator(
                "[0-9]{7}-?[0-9]{1}$", "invalid_company_id", "y-tunnus"
            ),
        ]

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

    def create(self, validated_data):
        entries_data = validated_data.pop("entries")
        targets = validated_data.pop("targets")
        attachments = validated_data.pop("attachments", [])
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
            try:
                root_section = Section.get_root(
                    Section.objects.get(
                        identifier=section_identifier, form=validated_data.get("form")
                    )
                )
                field = Field.objects.get(
                    identifier=field_identifier,
                    section__identifier=section_identifier,
                    section__form=validated_data.get("form"),
                )
            except Field.DoesNotExist:
                raise ValueError
            entry_section, unused = EntrySection.objects.get_or_create(
                identifier=root_section.identifier,
                answer=answer,
                defaults={"metadata": metadata},
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
        return answer

    def update(self, instance, validated_data):
        entries_data = validated_data.pop("entries", [])

        for (
            field_identifier,
            section_identifier,
            value,
            metadata,
            path,
        ) in self.entry_generator(entries_data):
            try:
                field = Field.objects.get(
                    identifier=field_identifier,
                    section__identifier=section_identifier,
                    section__form=validated_data.get("form"),
                )
                root_section = Section.get_root(
                    Section.objects.get(
                        identifier=section_identifier, form=validated_data.get("form")
                    )
                )
            except Field.DoesNotExist:
                raise ValueError
            entry_section, unused = EntrySection.objects.get_or_create(
                identifier=root_section.identifier,
                answer=instance,
                defaults={"metadata": metadata},
            )
            Entry.objects.update_or_create(
                entry_section=entry_section,
                field=field,
                defaults={"value": value["value"], "extra_value": value["extraValue"]},
                path=path,
            )

        instance.ready = validated_data.get("ready", instance.ready)
        instance.user = self.context["request"].user
        instance.save()
        return instance


class ApplicationStatusSerializer(serializers.HyperlinkedModelSerializer):
    identifier = serializers.CharField(source="plot_search_target.plan_unit.identifier")
    address = serializers.SerializerMethodField()
    geometry = GeometryField(source="plot_search_target.plan_unit.geometry")

    def get_address(self, obj):
        if obj.plot_search_target.plan_unit is None:
            return None
        lease_address = (
            obj.plot_search_target.plan_unit.lease_area.addresses.all()
            .order_by("-is_primary")
            .values("address")
            .first()
        )
        return lease_address

    class Meta:
        model = ApplicationStatus
        fields = (
            "identifier",
            "address",
            "reserved",
            "geometry",
        )


class AnswerListSerializer(serializers.ModelSerializer):
    applicant = serializers.SerializerMethodField()
    targets = ApplicationStatusSerializer(many=True, source="statuses")
    plot_search = serializers.SerializerMethodField()
    plot_search_type = serializers.SerializerMethodField()
    plot_search_subtype = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = (
            "id",
            "plot_search",
            "plot_search_type",
            "plot_search_subtype",
            "applicant",
            "targets",
        )

    @staticmethod
    def get_applicant(obj):
        try:
            applicant_section = obj.entry_sections.get(
                entries__field__identifier="hakija",
                entries__field__section__identifier="hakijan-tiedot",
            )
            applicant_type = applicant_section.sections.get(
                field__identifier="hakija", field__section__identifier="hakijan-tiedot"
            ).value
            if applicant_type == "Yritys":
                applicant = (
                    applicant_section.entries.filter(
                        entries__field__identifier="yrityksen-nimi",
                        entries__field__section__identifier="yrityksen-tiedot",
                    )
                    .first()
                    .value
                )
            elif applicant_type == "Henkilö":
                front_name = (
                    applicant_section.entries.filter(
                        entries__field__identifier="etunimi",
                        entries__field__section__identifier="henkilon-tiedot",
                    )
                    .first()
                    .value
                )
                last_name = (
                    applicant_section.entries.filter(
                        entries__field__identifier="sukunimi",
                        entries__field__section__identifier="henkilon-tiedot",
                    )
                    .first()
                    .value
                )
                applicant = " ".join([front_name, last_name])
            else:
                applicant = ""
        except EntrySection.DoesNotExist:
            applicant = ""
        return applicant

    def get_plot_search(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search = obj.form.plotsearch
        return plot_search.name

    def get_plot_search_type(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search_type = obj.form.plotsearch.subtype.plot_search_type
        return plot_search_type.name

    def get_plot_search_subtype(self, obj):
        if obj.form is None or not hasattr(obj.form, "plotsearch"):
            return None
        plot_search_subtype = obj.form.plotsearch.subtype
        return plot_search_subtype.name


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
        )

    def save(self, **kwargs):
        kwargs["user"] = self.context["request"].user
        return super().save(**kwargs)


class ReadAttachmentSerializer(AttachmentSerializer):
    field = serializers.CharField(source="field.identifier")
