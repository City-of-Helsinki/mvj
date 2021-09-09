# Register your models here.
from django.contrib.gis import admin, forms

from forms.models import (
    Field,
    Form,
    FieldType,
    Section,
    Choice,
)


class FieldTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


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
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "type":
            return FieldTypeChoiceField(queryset=FieldType.objects.all())
        elif db_field.name == "section":
            return SectionChoiceField(queryset=Section.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SectionModelAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            return SectionChoiceField(queryset=Section.objects.all())
        elif db_field.name == "form":
            return FormChoiceField(queryset=Form.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ChoiceModelAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "field":
            return FieldChoiceField(queryset=Field.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Field, FieldModelAdmin)
admin.site.register(Form, admin.ModelAdmin)
admin.site.register(FieldType, admin.ModelAdmin)
admin.site.register(Section, SectionModelAdmin)
admin.site.register(Choice, ChoiceModelAdmin)
