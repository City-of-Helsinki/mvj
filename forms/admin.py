# Register your models here.
from django.contrib.gis import admin, forms
from nested_inline.admin import (
    NestedModelAdmin,
    NestedStackedInline,
    NestedTabularInline,
)

from forms.models import Choice, Field, Form, Section


class FieldChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.label


class SectionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.title


class FormChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class FieldModelAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "section",
    )
    raw_id_fields = ("section",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "section":
            return SectionChoiceField(queryset=Section.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SectionModelAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "form",
    )
    list_filter = ("form",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            return SectionChoiceField(queryset=Section.objects.all())
        elif db_field.name == "form":
            return FormChoiceField(queryset=Form.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("form")


class ChoiceModelAdmin(admin.ModelAdmin):
    list_display = ("text",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "field":
            return FieldChoiceField(queryset=Field.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ChoiceInline(NestedTabularInline):
    model = Choice
    extra = 1
    fk_name = "field"


class FieldInline(NestedStackedInline):
    model = Field
    extra = 1
    fk_name = "section"
    inlines = [ChoiceInline]


class SectionInline(NestedStackedInline):
    model = Section
    extra = 1
    fk_name = "form"
    inlines = [FieldInline]


class FormModelAdmin(NestedModelAdmin):
    list_display = ("name",)
    model = Form
    inlines = [SectionInline]


admin.site.register(Field, FieldModelAdmin)
admin.site.register(Form, FormModelAdmin)
admin.site.register(Section, SectionModelAdmin)
admin.site.register(Choice, ChoiceModelAdmin)
