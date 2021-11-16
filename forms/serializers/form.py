from enumfields.drf.serializers import EnumSerializerField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from ..enums import FormState
from ..models import Answer, Choice, Entry, Field, FieldType, Form, Section
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
        fields = ("answer", "field", "value")
        validators = [
            UniqueTogetherValidator(
                queryset=Entry.objects.all().filter(answer=None),
                fields=["field", "value"],
            )
        ]


class AnswerSerializer(serializers.ModelSerializer):

    entries = EntrySerializer(many=True)

    class Meta:
        model = Answer
        fields = ("form", "user", "entries", "ready")
        validators = [
            RequiredFormFieldValidator(),
            FieldRegexValidator(
                "^[0-9]{6}[+Aa-][0-9]{3}[A-z0-9]$", "invalid_ssn", "henkilotunnus"
            ),
            FieldRegexValidator(
                "[0-9]{7}-?[0-9]{1}$", "invalid_company_id", "y-tunnus"
            ),
        ]

    def create(self, validated_data):
        entries_data = validated_data.pop("entries")
        answer = Answer.objects.create(**validated_data)
        for entry in entries_data:
            Entry.objects.create(answer=answer, **entry)
        return answer

    def update(self, instance, validated_data):
        for entry_data in validated_data.pop("entries", []):
            entry, created = Entry.objects.get_or_create(
                answer=instance, field=entry_data["field"]
            )
            entry.value = entry_data["value"]
            entry.save()
        instance.ready = validated_data.get("ready", instance.ready)
        instance.user = validated_data.get("user", instance.user)
        instance.save()
        return instance
