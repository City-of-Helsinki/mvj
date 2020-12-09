from rest_framework import serializers

from ..models import Choice, Field, Form, Section


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("text", "value", "action", "has_text_input")


class FieldSerializer(serializers.ModelSerializer):
    type = serializers.ReadOnlyField(source="type.identifier", read_only=True)
    choices = ChoiceSerializer(source="choice_set", many=True, read_only=True)

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
        )


class SectionSerializer(serializers.ModelSerializer):
    subsections = RecursiveSerializer(many=True, read_only=True)
    fields = FieldSerializer(source="field_set", many=True, read_only=True)

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
        )


class FormSerializer(serializers.ModelSerializer):

    sections = serializers.SerializerMethodField()

    def get_sections(self, form):
        qs = (
            Section.objects.select_related("parent")
            .filter(form=form)
            .filter(parent=None)
        )
        serializer = SectionSerializer(instance=qs, many=True)
        return serializer.data

    class Meta:
        model = Form
        fields = ("id", "name", "is_template", "title", "sections")
