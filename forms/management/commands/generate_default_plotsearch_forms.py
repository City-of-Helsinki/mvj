import copy
import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from forms.enums import FormState
from forms.models import Choice, Field, FieldType, Form, Section


class Command(BaseCommand):
    help = "Generates the default form templates for plot searches"

    DEFAULT_FORM_NAMES = {
        "default": "Tonttihaun peruslomake",
        "company": "Tonttihaun peruslomake vain yrityksille",
        "person": "Tonttihaun peruslomake vain yksityishenkilöille",
    }

    DEFAULT_FIELD_TYPES = (
        {"name": "Murtoluku", "identifier": "fractional"},
        {"name": "Lataa tiedosto", "identifier": "uploadfiles"},
        {"name": "Radiopainike linjassa", "identifier": "radiobuttoninline"},
        {"name": "Radiopainike", "identifier": "radiobutton"},
        {"name": "Valintaruutu", "identifier": "checkbox"},
        {"name": "Alasvetovalikko", "identifier": "dropdown"},
        {"name": "Tekstialue", "identifier": "textarea"},
        {"name": "Tekstikenttä", "identifier": "textbox"},
        {"name": "Piilotettu", "identifier": "hidden"},
    )

    with open(
        "forms/management/commands/default_plotsearch_form_sections.json"
    ) as sections_json:
        DEFAULT_SECTIONS_AND_FIELDS = json.load(sections_json)

    def __init__(self, *args, **kwargs) -> None:
        self.form = None
        self.field_type_map = {}
        self.new_fields_generated = 0
        self.sections = None

        super().__init__(*args, **kwargs)

    def generate_form(self, form_type):
        try:
            old_form = Form.objects.get(
                name=self.DEFAULT_FORM_NAMES[form_type], is_template=True
            )
            old_form.delete()
        except ObjectDoesNotExist:
            pass

        self.form = Form.objects.create(
            name=self.DEFAULT_FORM_NAMES[form_type],
            description="",
            is_template=True,
            state=FormState.WORK_IN_PROGRESS,
            title=self.DEFAULT_FORM_NAMES[form_type],
            is_area_form=False,
        )

        self.sections = copy.deepcopy(self.DEFAULT_SECTIONS_AND_FIELDS)

    def generate_field_types(self):
        for field_type in self.DEFAULT_FIELD_TYPES:
            obj, created = FieldType.objects.get_or_create(
                name=field_type["name"], identifier=field_type["identifier"]
            )
            self.field_type_map[obj.identifier] = obj
            if created:
                self.new_fields_generated += 1

    def generate_choice(self, choice, parent_field):
        Choice.objects.create(field=parent_field, **choice)

    def generate_field(self, field, parent_section):
        field_type = field.pop("type")
        choices = field.pop("choices", [])
        new_field = Field.objects.create(
            section=parent_section, type=self.field_type_map[field_type], **field
        )
        for choice in choices:
            self.generate_choice(choice, new_field)

    def generate_section(self, section, form_type, parent=None):
        subsections = section.pop("subsections", [])
        fields = section.pop("fields", [])
        if section["identifier"] == "hakijan-tiedot" and form_type != "default":
            for field in fields:
                if field["identifier"] == "hakija":
                    field["type"] = "hidden"
                    field["default_value"] = "1" if form_type == "company" else "2"

        new_section = Section.objects.create(parent=parent, form=self.form, **section)
        for subsection in subsections:
            self.generate_section(subsection, form_type, new_section)

        for field in fields:
            self.generate_field(field, new_section)

    def generate_sections(self, form_type):
        for section in self.sections["sections"]:
            self.generate_section(section, form_type)

    def handle(self, *args, **options):
        self.stdout.write("Generating default plot search form templates..")
        self.generate_field_types()
        self.stdout.write(
            "{} new field types generated.".format(self.new_fields_generated)
        )
        for form_type in self.DEFAULT_FORM_NAMES.keys():
            self.generate_form(form_type)
            self.generate_sections(form_type)
            self.stdout.write("{}-form is done!".format(form_type))
