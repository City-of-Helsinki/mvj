import datetime

import factory
import pytest
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from pytest_factoryboy import register

from forms.models import Answer, Choice, Entry, Field, FieldType, Form, Section
from forms.models.form import EntrySection
from forms.tests.conftest import fake
from leasing.enums import (
    ContactType,
    LeaseAreaType,
    LocationType,
    PlotSearchTargetType,
    TenantContactType,
)
from leasing.models import (
    Contact,
    Decision,
    Lease,
    LeaseArea,
    PlanUnit,
    Tenant,
    TenantContact,
)
from leasing.models.land_area import LeaseAreaAddress
from plotsearch.models import (
    AreaSearch,
    IntendedSubUse,
    IntendedUse,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    TargetInfoLink,
)
from users.models import User


@pytest.fixture
def plot_search_test_data(
    plot_search_factory,
    plot_search_type_factory,
    plot_search_subtype_factory,
    plot_search_stage_factory,
    user_factory,
):
    plot_search_type = plot_search_type_factory(name="Test type")
    plot_search_subtype = plot_search_subtype_factory(
        name="Test subtype", plot_search_type=plot_search_type
    )
    plot_search_stage = plot_search_stage_factory(name="Test stage")
    preparer = user_factory(username="test_preparer")

    begin_at = (timezone.now() + timezone.timedelta(days=7)).replace(microsecond=0)
    end_at = (begin_at + timezone.timedelta(days=7)).replace(microsecond=0)

    plot_search = plot_search_factory(
        name="PS1",
        subtype=plot_search_subtype,
        stage=plot_search_stage,
        begin_at=begin_at,
        end_at=end_at,
    )
    plot_search.preparers.add(preparer)

    return plot_search


@pytest.fixture
def area_search_test_data(
    area_search_factory, intended_use_factory, intended_sub_use_factory, user_factory
):
    intended_use = intended_use_factory()
    intended_sub_use = intended_sub_use_factory(intended_use=intended_use)
    area_search = area_search_factory(
        description_area=fake.name(),
        description_intended_use=fake.name(),
        intended_use=intended_sub_use,
        geometry=GEOSGeometry(
            "MULTIPOLYGON (((24.967535 60.174334, 24.966888 60.173293, 24.970275 60.172791, 24.970922 60.17412, 24.967535 60.174334)))"  # noqa: E501
        ),
    )

    return area_search


@register
class AreaSearchFactory(factory.DjangoModelFactory):
    class Meta:
        model = AreaSearch


@register
class IntendedUseFactory(factory.DjangoModelFactory):
    class Meta:
        model = IntendedUse


@register
class IntendedSubUseFactory(factory.DjangoModelFactory):
    class Meta:
        model = IntendedSubUse


@register
class PlotSearchFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearch


@register
class PlotSearchTargetFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget


@register
class PlotSearchTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchType


@register
class PlotSearchSubtypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchSubtype


@register
class PlotSearchStageFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchStage


@register
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


@register
class PlanUnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlanUnit


@pytest.fixture
def lease_test_data(
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    lease_area_factory,
    lease_area_address_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=29, notice_period_id=1
    )

    contacts = [
        contact_factory(
            first_name="Lessor First name",
            last_name="Lessor Last name",
            is_lessor=True,
            type=ContactType.PERSON,
        )
    ]
    for i in range(4):
        contacts.append(
            contact_factory(
                first_name="First name " + str(i),
                last_name="Last name " + str(i),
                type=ContactType.PERSON,
            )
        )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    tenants = [tenant1, tenant2]

    tenantcontacts = [
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant1,
            contact=contacts[1],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[2],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.CONTACT,
            tenant=tenant2,
            contact=contacts[3],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[4],
            start_date=timezone.now().date()
            + datetime.timedelta(days=30),  # Future tenant
        ),
    ]

    lease.tenants.set(tenants)
    lease_area = lease_area_factory(
        lease=lease, identifier="12345", area=1000, section_area=1000,
    )

    lease_area_address_factory(lease_area=lease_area, address="Test street 1")
    lease_area_address_factory(
        lease_area=lease_area, address="Primary street 1", is_primary=True
    )

    return {
        "lease": lease,
        "lease_area": lease_area,
        "tenants": tenants,
        "tenantcontacts": tenantcontacts,
    }


@pytest.fixture
def plot_search_target(
    plan_unit_factory,
    plot_search_target_factory,
    lease_test_data,
    plot_search_test_data,
):
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    plot_search_target = plot_search_target_factory(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    return plot_search_target


@register
class LeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Lease


@register
class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact


@register
class TenantFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tenant


@register
class TenantContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenantContact


@register
class LeaseAreaAddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = LeaseAreaAddress


@register
class LeaseAreaFactory(factory.DjangoModelFactory):
    type = LeaseAreaType.REAL_PROPERTY
    location = LocationType.SURFACE

    class Meta:
        model = LeaseArea


@register
class FormFactory(factory.DjangoModelFactory):
    class Meta:
        model = Form


@register
class DecisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Decision


@register
class InfoLinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = TargetInfoLink


@register
class SectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Section


@register
class FieldFactory(factory.DjangoModelFactory):
    class Meta:
        model = Field


@register
class FieldTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = FieldType


@pytest.fixture
def basic_answer(
    answer_factory,
    entry_section_factory,
    entry_factory,
    basic_template_form,
    user_factory,
):
    form = basic_template_form
    user = user_factory(username=fake.name())
    answer = answer_factory(form=form, user=user)
    entry_section = None

    for section in answer.form.sections.all():
        if not EntrySection.objects.filter(
            identifier=section.get_root(section).identifier
        ).exists():
            entry_section = entry_section_factory(
                answer=answer, identifier=section.get_root(section).identifier
            )
        for field in section.fields.all():
            entry_factory(entry_section=entry_section, field=field, value=fake.name())

    return answer


@register
class EntryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Entry


@register
class EntrySectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = EntrySection


@register
class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer


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
        title="Hakijan tiedot",
        add_new_allowed=True,
        add_new_text="Add new applicant",
        identifier="hakijan-tiedot",
    )

    # Company applicant
    company_applicant_section = section_factory(
        form=form,
        parent=applicant_section,
        title="Company information",
        visible=False,
        identifier="company-information",
    )
    field_factory(
        label="Company name",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="company-name",
    )
    field_factory(
        label="Business ID",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="business-id",
    )
    field_factory(
        label="Language",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="language",
    )
    field_factory(
        label="Y-tunnus",
        section=company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="y-tunnus",
    )

    # Subsection for company's contact person information
    contact_person_company_applicant_section = section_factory(
        form=form,
        parent=company_applicant_section,
        title="Contact person",
        identifier="contact-person",
    )
    field_factory(
        label="First name",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name",
    )
    field_factory(
        label="Last name",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name",
    )
    field_factory(
        label="Personal identity code",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="personal-identity-code",
    )
    field_factory(
        label="Henkilötunnus",
        section=contact_person_company_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="henkilotunnus",
    )

    # Person applicant
    person_applicant_section = section_factory(
        form=form,
        parent=applicant_section,
        title="Person information",
        visible=False,
        identifier="person-information",
    )
    field_factory(
        label="First name",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name-1",
    )
    field_factory(
        label="Last name",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name-1",
    )
    field_factory(
        label="Personal identity code",
        section=person_applicant_section,
        type=basic_field_types["textbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="personal-identity-code-1",
    )

    # Subsection for person's contact person information
    person_contact_person_section = section_factory(
        form=form,
        parent=person_applicant_section,
        title="Contact person",
        identifier="contact-person",
    )
    field_factory(
        label="Different than applicant",
        section=person_contact_person_section,
        type=basic_field_types["checkbox"],
        action="ToggleEnableInSection=" + person_contact_person_section.identifier,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        identifier="different-than-applicant",
    )
    field_factory(
        label="First name",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name-2",
    )
    field_factory(
        label="Last name",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name-2",
    )
    field_factory(
        label="Personal identity code",
        section=person_contact_person_section,
        type=basic_field_types["textbox"],
        enabled=False,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="personal-identity-code-2",
    )

    additional_info_applicant_section = section_factory(
        form=form,
        parent=applicant_section,
        title="Additional information",
        identifier="additional-information",
    )
    field_factory(
        label="Additional information",
        section=additional_info_applicant_section,
        type=basic_field_types["textarea"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="additional-information",
    )

    # Applicant switcher: Company / Person
    applicant_type_switcher_field = field_factory(
        section=applicant_section,
        type=basic_field_types["radiobuttoninline"],
        label=fake.name(),
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="applicant-switch",
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
    application_target_section = section_factory(
        form=form, title="Application target", identifier="application-target"
    )

    target_previously_received_when_field = field_factory(
        label="Have you previously received a plot of land from the city?",
        section=application_target_section,
        type=basic_field_types["radiobuttoninline"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="have-you-ever",
    )
    choice_factory(
        field=target_previously_received_when_field,
        text="No",
        value="1",
        action=fake.sentence(),
    )
    choice_factory(
        field=target_previously_received_when_field,
        text="Yes",
        value="2",
        has_text_input=True,
        action=fake.sentence(),
    )

    plot_what_application_applies_field = field_factory(
        label="The plot what the application applies",
        section=application_target_section,
        type=basic_field_types["dropdown"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="the-plot-what",
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Plot A",
        value="1",
        action=fake.sentence(),
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Plot B",
        value="2",
        action=fake.sentence(),
    )

    field_factory(
        label="%-grounds",
        section=application_target_section,
        type=basic_field_types["textbox"],
        hint_text="€/k-m2",
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="percentage-grounds",
    )
    field_factory(
        label="Form of financing and management",
        section=application_target_section,
        type=basic_field_types["checkbox"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="form-of-financing",
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Form A",
        value="1",
        action=fake.sentence(),
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Form B",
        value="2",
        action=fake.sentence(),
    )
    choice_factory(
        field=plot_what_application_applies_field,
        text="Other:",
        value="3",
        has_text_input=True,
        action=fake.sentence(),
    )

    field_factory(
        label="Reference attachments",
        section=application_target_section,
        type=basic_field_types["uploadfiles"],
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="reference-attachments",
    )

    return form


@register
class ChoiceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Choice


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
