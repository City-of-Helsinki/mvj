from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from ..models import Answer, Choice, Entry, Field, Form, Section


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
