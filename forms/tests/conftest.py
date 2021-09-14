import factory
import pytest
from faker import Faker
from pytest_factoryboy import register

from forms.models.form import Answer, Choice, Entry, Field, FieldType, Form, Section

fake = Faker("fi_FI")


@register
class ChoiceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Choice


@register
class FieldFactory(factory.DjangoModelFactory):
    class Meta:
        model = Field


@register
class FieldTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = FieldType


@register
class FormFactory(factory.DjangoModelFactory):
    class Meta:
        model = Form


@register
class SectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Section


@register
class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer


@register
class EntryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Entry


@pytest.fixture
def basic_template_form(
    form_factory, section_factory, field_factory, choice_factory, basic_field_types,
):
    form = form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )

    # Root applicant section
    applicant_section = section_factory(
        form=form,
        title="Applicant information",
        add_new_allowed=True,
        add_new_text="Add new applicant",
    )

    # Company applicant
    company_applicant_section = section_factory(
        form=form, parent=applicant_section, title="Company information", visible=False
    )
    field_factory(
        label="Company name",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Business ID",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Language",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
    )

    # Subsection for company's contact person information
    contact_person_company_applicant_section = section_factory(
        form=form, parent=company_applicant_section, title="Contact person"
    )
    field_factory(
        label="First name",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Last name",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Personal identity code",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
    )

    # Person applicant
    person_applicant_section = section_factory(
        form=form, parent=applicant_section, title="Person information", visible=False
    )
    field_factory(
        label="First name",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Last name",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
    )
    field_factory(
        label="Personal identity code",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
    )

    # Subsection for person's contact person information
    person_contact_person_section = section_factory(
        form=form, parent=person_applicant_section, title="Contact person"
    )
    field_factory(
        label="Different than applicant",
        section=person_contact_person_section,
        type=basic_field_types["checkbox"],
        action="ToggleEnableInSection=" + person_contact_person_section.identifier,
    )
    field_factory(
        label="First name",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
    )
    field_factory(
        label="Last name",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
    )
    field_factory(
        label="Personal identity code",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
    )

    additional_info_applicant_section = section_factory(
        form=form, parent=applicant_section, title="Additional information",
    )
    field_factory(
        label="Additional information",
        section=additional_info_applicant_section,
        type=basic_field_types["textarea"],
    )

    # Applicant switcher: Company / Person
    applicant_type_switcher_field = field_factory(
        section=applicant_section, type=basic_field_types["radiobuttoninline"],
    )
    choice_factory(
        field=applicant_type_switcher_field,
        text="Company",
        value="1",
        action="ShowSection="
        + company_applicant_section.identifier
        + ", HideSection="
        + person_applicant_section.identifier,
    )
    choice_factory(
        field=applicant_type_switcher_field,
        text="Person",
        value="2",
        action="ShowSection="
        + person_applicant_section.identifier
        + ", HideSection="
        + company_applicant_section.identifier,
    )

    # Root application target section
    application_target_section = section_factory(form=form, title="Application target",)

    target_previously_received_when_field = field_factory(
        label="Have you previously received a plot of land from the city?",
        section=application_target_section,
        type=basic_field_types["radiobuttoninline"],
    )
    choice_factory(
        field=target_previously_received_when_field, text="No", value="1",
    )
    choice_factory(
        field=target_previously_received_when_field,
        text="Yes",
        value="2",
        has_text_input=True,
    )

    plot_what_application_applies_field = field_factory(
        label="The plot what the application applies",
        section=application_target_section,
        type=basic_field_types["dropdown"],
    )
    choice_factory(
        field=plot_what_application_applies_field, text="Plot A", value="1",
    )
    choice_factory(
        field=plot_what_application_applies_field, text="Plot B", value="2",
    )

    field_factory(
        label="%-grounds",
        section=application_target_section,
        type=basic_field_types["textbox"],
        hint_text="€/k-m2",
    )
    field_factory(
        label="Form of financing and management",
        section=application_target_section,
        type=basic_field_types["checkbox"],
    )
    choice_factory(
        field=plot_what_application_applies_field, text="Form A", value="1",
    )
    choice_factory(
        field=plot_what_application_applies_field, text="Form B", value="2",
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Other:",
        value="3",
        has_text_input=True,
    )

    field_factory(
        label="Reference attachments",
        section=application_target_section,
        type=basic_field_types["uploadfiles"],
    )

    return form


@pytest.fixture
def basic_field_types(field_type_factory):
    field_types = []
    field = field_type_factory(name="Textbox", identifier="textbox")
    field_types.append(field)
    field = field_type_factory(name="Textarea", identifier="textarea")
    field_types.append(field)
    field = field_type_factory(name="Checkbox", identifier="checkbox")
    field_types.append(field)
    field = field_type_factory(name="Dropdown", identifier="dropdown")
    field_types.append(field)
    field = field_type_factory(name="Radiobutton", identifier="radiobutton")
    field_types.append(field)
    field = field_type_factory(name="RadiobuttonInline", identifier="radiobuttoninline")
    field_types.append(field)

    # Special
    field = field_type_factory(name="Upload Files", identifier="uploadfiles")
    field_types.append(field)

    return {t.identifier: t for t in field_types}
