import datetime
import json

import factory
import pytest
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GEOSGeometry
from django.urls import reverse
from django.utils import timezone
from pytest_factoryboy import register

from batchrun.models import Command, Job, JobRun, JobRunLog
from file_operations.models.filescan import FileScanStatus
from forms.models import Answer, Choice, Entry, Field, Form, Section
from forms.models.form import Attachment, EntrySection
from forms.tests.conftest import fake
from forms.utils import EmailMessageInput
from leasing.enums import (
    ContactType,
    LeaseAreaType,
    LocationType,
    PlotSearchTargetType,
    TenantContactType,
)
from leasing.models import (
    CollectionLetter,
    Contact,
    CustomDetailedPlan,
    Decision,
    District,
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationLease,
    Inspection,
    Lease,
    LeaseArea,
    LeaseType,
    Municipality,
    PlanUnit,
    PlanUnitIntendedUse,
    ServiceUnit,
    Tenant,
    TenantContact,
)
from leasing.models.land_area import LeaseAreaAddress
from leasing.models.receivable_type import ReceivableType
from plotsearch.models import (
    AreaSearch,
    AreaSearchAttachment,
    AreaSearchIntendedUse,
    Favourite,
    InformationCheck,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    RelatedPlotApplication,
    TargetInfoLink,
    TargetStatus,
)
from users.models import User


@pytest.fixture()
def admin_client(db, admin_user):
    """A Django test client logged in as an admin user.

    Copied from pytest-django and added the default ServiceUnit to admin_users
    service units."""
    from django.test.client import Client

    from leasing.models import ServiceUnit

    try:
        admin_user.service_units.set([ServiceUnit.objects.get(pk=1)])
    except ServiceUnit.DoesNotExist:
        service_unit = ServiceUnitFactory()
        admin_user.service_units.set([service_unit])

    client = Client()
    client.login(username=admin_user.username, password="password")
    return client


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
    plot_search.save()

    return plot_search


@pytest.fixture
def area_search_test_data(
    area_search_factory,
    area_search_intended_use_factory,
    answer_factory,
    form_factory,
    user_factory,
):
    intended_use = area_search_intended_use_factory()
    form = form_factory(title=fake.name())
    user = user_factory(username=fake.name())
    area_search = area_search_factory(
        description_area=fake.name(),
        description_intended_use=fake.name(),
        intended_use=intended_use,
        geometry=GEOSGeometry(
            "MULTIPOLYGON (((24.967535 60.174334, 24.966888 60.173293, 24.970275 60.172791, 24.970922 60.17412, 24.967535 60.174334)))"  # noqa: E501
        ),
        answer=answer_factory(form=form, user=user),
    )

    return area_search


# Batchrun model factories
@register
class CommandFactory(factory.django.DjangoModelFactory):
    type = "django-manage"

    class Meta:
        model = Command


@register
class JobFactory(factory.django.DjangoModelFactory):
    command = factory.SubFactory(CommandFactory)

    class Meta:
        model = Job


@register
class JobRunFactory(factory.django.DjangoModelFactory):
    job = factory.SubFactory(JobFactory)

    class Meta:
        model = JobRun


@register
class JobRunLogFactory(factory.django.DjangoModelFactory):
    run = factory.SubFactory(JobRunFactory)

    class Meta:
        model = JobRunLog


@register
class AreaSearchIntendedUseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AreaSearchIntendedUse


@register
class AreaSearchFactory(factory.django.DjangoModelFactory):
    intended_use = factory.SubFactory(AreaSearchIntendedUseFactory)

    class Meta:
        model = AreaSearch


@register
class AreaSearchAttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AreaSearchAttachment


@register
class FavouriteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Favourite


@register
class LeaseTypeFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "A%10d" % n)

    class Meta:
        model = LeaseType


@register
class MunicipalityFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "1%1d" % n)

    class Meta:
        model = Municipality


@register
class DistrictFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "10%1d" % n)
    municipality = factory.SubFactory(MunicipalityFactory)

    class Meta:
        model = District


@register
class PlotSearchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearch


@register
class LeaseFactory(factory.django.DjangoModelFactory):
    type = factory.SubFactory(LeaseTypeFactory)
    municipality = factory.SubFactory(MunicipalityFactory)
    district = factory.SubFactory(DistrictFactory)

    @factory.lazy_attribute
    def service_unit(self):
        from leasing.models import ServiceUnit

        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = Lease


@register
class ServiceUnitFactory(factory.django.DjangoModelFactory):
    id = factory.Sequence(lambda n: n + 100)

    class Meta:
        model = ServiceUnit


@register
class LeaseWithGeneratedServiceUnitFactory(factory.django.DjangoModelFactory):
    """
    Created to circumvent the existing LeaseFactory, which hardcodes the
    service unit id to 1, which is expected to match service unit "MaKe".

    Feel free to replace that implementation with this one, and fix all the old
    tests at the same time.
    """

    type = factory.SubFactory(LeaseTypeFactory)
    municipality = factory.SubFactory(MunicipalityFactory)
    district = factory.SubFactory(DistrictFactory)
    service_unit = factory.SubFactory(ServiceUnitFactory)

    class Meta:
        model = Lease


@register
class LeaseAreaFactory(factory.django.DjangoModelFactory):
    type = LeaseAreaType.REAL_PROPERTY
    location = LocationType.SURFACE
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease = factory.SubFactory(LeaseFactory)

    class Meta:
        model = LeaseArea


@register
class PlanUnitIntendedUseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanUnitIntendedUse


@register
class PlanUnitFactory(factory.django.DjangoModelFactory):
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease_area = factory.SubFactory(LeaseAreaFactory)
    plan_unit_intended_use = factory.SubFactory(PlanUnitIntendedUseFactory)
    identifier = factory.Iterator(
        ["91-1-30-1", "91-1-30-2", "91-1-30-3", "91-1-30-4", "91-1-30-5"]
    )

    class Meta:
        model = PlanUnit


@register
class CustomDetailedPlanFactory(factory.django.DjangoModelFactory):
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease_area = factory.SubFactory(LeaseAreaFactory)
    rent_build_permission = factory.Sequence(lambda n: n)
    intended_use = factory.SubFactory(PlanUnitIntendedUseFactory)

    class Meta:
        model = CustomDetailedPlan


@register
class PlotSearchTargetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget


@register
class PlotSearchTargetFactoryWithSubFactories(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget

    plot_search = factory.SubFactory(PlotSearchFactory)
    plan_unit = factory.SubFactory(PlanUnitFactory)
    target_type = PlotSearchTargetType.SEARCHABLE


@register
class PlotSearchTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchType


@register
class PlotSearchSubtypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchSubtype


@register
class PlotSearchStageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchStage


@register
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    @factory.post_generation
    def service_units(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        for service_unit in extracted:
            self.service_units.add(service_unit)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.user_permissions.set(Permission.objects.filter(codename__in=extracted))


@register
class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group


@register
class ReceivableTypeFactory(factory.django.DjangoModelFactory):
    @factory.lazy_attribute
    def service_unit(self):
        from leasing.models import ServiceUnit

        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = ReceivableType


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
            start_date=timezone.datetime(year=2019, month=2, day=28),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[2],
            start_date=timezone.datetime(year=2019, month=2, day=28),
        ),
        tenant_contact_factory(
            type=TenantContactType.CONTACT,
            tenant=tenant2,
            contact=contacts[3],
            start_date=timezone.datetime(year=2019, month=2, day=28),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[4],
            start_date=timezone.datetime(year=2019, month=3, day=1)
            + datetime.timedelta(days=30),  # Future tenant
        ),
    ]

    lease.tenants.set(tenants)
    lease_area = lease_area_factory(
        lease=lease,
        identifier="12345",
        area=1000,
        section_area=1000,
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
    plot_search_target_factory_with_sub_factories,
    lease_test_data,
    plot_search_test_data,
):
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    plot_search_target = plot_search_target_factory_with_sub_factories(
        plot_search=plot_search_test_data,
        plan_unit=plan_unit,
        target_type=PlotSearchTargetType.SEARCHABLE,
    )

    return plot_search_target


@register
class ContactFactory(factory.django.DjangoModelFactory):
    type = ContactType.PERSON

    @factory.lazy_attribute
    def service_unit(self):
        from leasing.models import ServiceUnit

        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = Contact


@register
class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant


@register
class TenantContactFactory(factory.django.DjangoModelFactory):
    tenant = factory.SubFactory(TenantFactory)
    contact = factory.SubFactory(ContactFactory)

    class Meta:
        model = TenantContact


@register
class LeaseAreaAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeaseAreaAddress


@register
class FormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Form


@register
class DecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Decision


@register
class InfoLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TargetInfoLink


@register
class SectionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = Section


@register
class FieldFactory(factory.django.DjangoModelFactory):
    section = factory.SubFactory(SectionFactory)

    class Meta:
        model = Field


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
class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Entry


@register
class EntrySectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntrySection


@register
class AnswerFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Answer


@register
class AttachmentFactory(factory.django.DjangoModelFactory):

    field = factory.SubFactory(FieldFactory)

    class Meta:
        model = Attachment


@pytest.fixture
def basic_template_form(
    form_factory,
    section_factory,
    field_factory,
    choice_factory,
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
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="company-name",
    )
    field_factory(
        label="Business ID",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="business-id",
    )
    field_factory(
        label="Language",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="language",
    )
    field_factory(
        label="Y-tunnus",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="y-tunnus",
    )
    field_factory(
        label="Hallintaosuus",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="hallintaosuus",
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
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name",
    )
    field_factory(
        label="Last name",
        section=contact_person_company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name",
    )
    field_factory(
        label="Personal identity code",
        section=contact_person_company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="personal-identity-code",
    )
    field_factory(
        label="Henkilötunnus",
        section=contact_person_company_applicant_section,
        type="textbox",
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
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name-1",
    )
    field_factory(
        label="Last name",
        section=person_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name-1",
    )
    field_factory(
        label="Personal identity code",
        section=person_applicant_section,
        type="textbox",
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
        type="checkbox",
        action="ToggleEnableInSection=" + person_contact_person_section.identifier,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        identifier="different-than-applicant",
    )
    field_factory(
        label="First name",
        section=person_contact_person_section,
        type="textbox",
        enabled=False,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="first-name-2",
    )
    field_factory(
        label="Last name",
        section=person_contact_person_section,
        type="textbox",
        enabled=False,
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="last-name-2",
    )
    field_factory(
        label="Personal identity code",
        section=person_contact_person_section,
        type="textbox",
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
        type="textarea",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="additional-information",
    )

    # Applicant switcher: Company / Person
    applicant_type_switcher_field = field_factory(
        section=applicant_section,
        type="radiobuttoninline",
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
        type="radiobuttoninline",
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
        type="dropdown",
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
        type="textbox",
        hint_text="€/k-m2",
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="percentage-grounds",
    )
    field_factory(
        label="Form of financing and management",
        section=application_target_section,
        type="checkbox",
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
        type="uploadfiles",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="reference-attachments",
    )

    return form


@pytest.fixture
def area_search_template_form(
    form_factory, section_factory, field_factory, choice_factory
):
    form = form_factory(
        name=fake.name(),
        description=fake.sentence(),
        is_template=True,
        title=fake.name(),
    )
    # ATTENTION:
    # When creating (some) these objects, it is good
    # to know that supplying the `identifier` might not
    # actually set it, due to some logic in models save().
    # Seems like the `title` is used to generate an identifier.

    # Root applicant section
    applicant_section = section_factory(
        form=form,
        title="Hakijan tiedot",
        add_new_allowed=True,
        add_new_text="Add new applicant",
        identifier="hakijan-tiedot",  # applicant-information
    )
    # Applicant switcher: Company / Person
    applicant_type_switcher_field = field_factory(
        section=applicant_section,
        type="radiobuttoninline",
        label="Hakijan tyyppi",  # Applicant type
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="hakija",  # applicant
    )
    choice_factory(
        field=applicant_type_switcher_field,
        text="Yritys",  # Company
        value="1",
        action=f"ShowSection={applicant_section.identifier}",
    )
    choice_factory(
        field=applicant_type_switcher_field,
        text="Henkilö",  # Person
        value="2",
        action=f"ShowSection={applicant_section.identifier}",
    )

    # Company applicant
    company_applicant_section = section_factory(
        form=form,
        parent=applicant_section,
        title="Yrityksen tiedot",
        # visible=False,
        identifier="yrityksen-tiedot",  # company-information
    )
    field_factory(
        label="Yrityksen nimi",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="yrityksen-nimi",  # company-name
    )
    field_factory(
        label="Kieli",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="kieli",  # language
    )
    field_factory(
        label="Y-tunnus",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="y-tunnus",  # company-id
    )
    field_factory(
        label="Puhelinnumero",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="puhelinnumero",  # phone-number
    )
    field_factory(
        label="Sähköposti",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="sahkoposti",  # email
    )
    field_factory(
        label="Katuosoite",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="katuosoite",  # address
    )
    field_factory(
        label="Postinumero",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="postinumero",  # postal code
    )
    field_factory(
        label="Postitoimipaikka",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="postitoimipaikka",  # postal-district
    )
    field_factory(
        label="Maa",
        section=company_applicant_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="maa",  # country
    )
    field_factory(
        label="Hallintaosuus",
        section=company_applicant_section,
        type="fractional",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="hallintaosuus",  # control-share
    )

    # Subsection for company's billing information
    billing_information_section = section_factory(
        form=form,
        parent=company_applicant_section,
        title="Laskutustiedot",
        identifier="laskutustiedot",  # billing-information
    )
    field_factory(
        label="Kieli",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="kieli",  # language
    )
    field_factory(
        label="Puhelinnumero",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="puhelinnumero",  # phone-number
    )
    field_factory(
        label="Sähköposti",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="sahkoposti",  # email-address
    )
    field_factory(
        label="Katuosoite",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="katuosoite",  # road-address
    )
    field_factory(
        label="Postinumero",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="postinumero",  # postal-code
    )
    field_factory(
        label="Postitoimipaikka",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="postitoimipaikka",  # postal-district
    )
    field_factory(
        label="Maa",
        section=billing_information_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="maa",  # country
    )
    # Subsection for company's billing reference
    billing_reference_section = section_factory(
        form=form,
        parent=billing_information_section,
        title="Laskutusviite",
        identifier="laskutusviite",  # billing-reference
    )
    field_factory(
        label="Verkkolaskutusosoite",
        section=billing_reference_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="verkkolaskutusosoite",  # online-billin-address
    )
    field_factory(
        label="Laskutusviite",
        section=billing_reference_section,
        type="textbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="laskutusviite",  # billing-reference
    )

    # Root application target section
    application_decision_delivery_section = section_factory(
        form=form,
        title="Paatoksen toimitus",
        identifier="paatoksen-toimitus",  # decision-delivery
    )
    field_factory(
        label="Sahkoisesti ilmoittamaani sahkopostiosoitteeseen",
        section=application_decision_delivery_section,
        type="checkbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen",  # by-email
    )
    field_factory(
        label="Postitse ilmoittamaani postiosoitteeseen",
        section=application_decision_delivery_section,
        type="checkbox",
        hint_text=fake.sentence(),
        validation=fake.sentence(),
        action=fake.sentence(),
        identifier="postitse-ilmoittamaani-postiosoitteeseen",  # by-mail
    )

    return form


@pytest.fixture
def area_search_form(area_search_template_form):
    form = area_search_template_form
    form.is_template = False
    form.save()
    return form


@register
class ChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Choice


@register
class TargetStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TargetStatus

    plot_search_target = factory.SubFactory(PlotSearchTargetFactoryWithSubFactories)
    answer = factory.SubFactory(AnswerFactory)


@register
class InformationCheckFactory(factory.django.DjangoModelFactory):
    entry_section = factory.SubFactory(EntrySectionFactory)

    class Meta:
        model = InformationCheck


@register
class RelatedPlotApplicationFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseFactory)
    content_object = factory.SubFactory(AreaSearchFactory, description_area="test")

    class Meta:
        model = RelatedPlotApplication


@pytest.fixture
def related_plot_application_test_data(
    lease_factory,
    area_search_factory,
    area_search_intended_use_factory,
    target_status_factory,
    related_plot_application_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )
    intended_use = area_search_intended_use_factory()
    area_search = area_search_factory(
        description_area=fake.name(),
        description_intended_use=fake.name(),
        intended_use=intended_use,
    )
    target_status = target_status_factory()
    related_plot_applications = []
    related_plot_applications.append(
        related_plot_application_factory(
            lease=lease,
            content_object=area_search,
        )
    )
    related_plot_applications.append(
        related_plot_application_factory(
            lease=lease,
            content_object=target_status,
        )
    )

    return {
        "lease": lease,
        "area_search": area_search,
        "target_status": target_status,
        "related_plot_applications": related_plot_applications,
    }


@pytest.fixture
def answer_with_email(
    admin_client,
    area_search_intended_use_factory,
    user_factory,
    area_search_form,
):
    user = user_factory(username=fake.name())
    intended_use = area_search_intended_use_factory(name="Urheilu- ja liikuntapaikat")

    area_search_payload = {
        "area_search_attachments": [],
        "geometry": (
            '{"coordinates":[[[[24.927311,60.188275],[24.928843,60.188204],[24.929369,60.186652],'
            "[24.928722,60.185772],[24.926181,60.185546],[24.924826,60.187116],[24.924482,60.187717],"
            "[24.92531,60.188472],[24.926571,60.188589],[24.927311,60.188275]]]],"
            '"type":"MultiPolygon"}'
        ),
        "start_date": "2023-11-06T22:00:00.000Z",
        "description_area": "Olympic stadium area",
        "description_intended_use": "Want to hold Helsinki Olympics 2028 here",
        "attachments": [],
        "intended_use": intended_use.id,
        "end_date": "2023-11-29T22:00:00.000Z",
    }

    url = reverse("v1:pub_area_search-list")
    response = admin_client.post(url, data=area_search_payload)
    area_search = AreaSearch.objects.get(id=response.data["id"])

    def _get_company_applicants(count=1):
        if count > 10:
            count = 10
        company_applicants = []
        emails = iter([f"user{i}@example.com" for i in range(1, 11)])
        company_ids = iter(
            [
                "3154053-6",
                "8527616-0",
                "7062724-7",
                "8253184-0",
                "4388112-7",
                "6833006-5",
                "6376250-4",
                "5281453-2",
                "8008574-4",
                "1274040-1",
                "1150642-9",
                "1561624-6",
                "4263272-7",
                "7720431-9",
                "4416074-3",
            ]
        )
        company_names = iter(
            [
                "Sepposen Betoni Oy",
                "Hattulan kultakaivos Oy",
                "Kuusamon bajamajat Ky",
                "Avaruusolioiden ystävät ry",
                "Wirren Wirkkuu Tmi",
                "Helsingin Olympialaiset 2028 Oy",
                "Oulun alakaupunki ry",
                "Heikin hiekka Ky",
                "George's Barbershop Oy",
                "Kytky-Kauppa Oy",
            ]
        )
        for _ in range(count):
            email = next(emails)
            company_id = next(company_ids)
            company_applicants.append(
                {
                    "sections": {
                        "yrityksen-tiedot": {
                            "sections": {
                                "laskutustiedot": {
                                    "sections": {
                                        "laskutusviite": {
                                            "sections": {},
                                            "fields": {
                                                "verkkolaskutusosoite": {
                                                    "value": "1122334455",
                                                    "extraValue": "",
                                                },
                                                "laskutusviite": {
                                                    "value": "99887766",
                                                    "extraValue": "",
                                                },
                                            },
                                        }
                                    },
                                    "fields": {
                                        "kieli": {"value": "suomi", "extraValue": ""},
                                        "puhelinnumero": {
                                            "value": "+123456789",
                                            "extraValue": "",
                                        },
                                        "sahkoposti": {
                                            "value": email,
                                            "extraValue": "",
                                        },
                                        "katuosoite": {
                                            "value": "Paavo Nurmen tie 2",
                                            "extraValue": "",
                                        },
                                        "maa": {"value": "", "extraValue": ""},
                                        "postitoimipaikka": {
                                            "value": "Helsinki",
                                            "extraValue": "",
                                        },
                                        "postinumero": {
                                            "value": "00250",
                                            "extraValue": "",
                                        },
                                    },
                                }
                            },
                            "fields": {
                                "yrityksen-nimi": {
                                    "value": next(company_names),
                                    "extraValue": "",
                                },
                                "y-tunnus": {"value": company_id, "extraValue": ""},
                                "kieli": {"value": "suomi", "extraValue": ""},
                                "puhelinnumero": {
                                    "value": "+123456789",
                                    "extraValue": "",
                                },
                                "sahkoposti": {"value": email, "extraValue": ""},
                                "katuosoite": {
                                    "value": "Paavo Nurmen tie 2",
                                    "extraValue": "",
                                },
                                "postinumero": {"value": "00250", "extraValue": ""},
                                "postitoimipaikka": {
                                    "value": "Helsinki",
                                    "extraValue": "",
                                },
                                "maa": {"value": "", "extraValue": ""},
                                "hallintaosuus": {
                                    "value": f"1 / {count}",
                                    "extraValue": "",
                                },
                            },
                        }
                    },
                    "fields": {"hakija": {"value": "1", "extraValue": ""}},
                    "metadata": {"applicantType": "company", "identifier": company_id},
                }
            )

        return company_applicants

    answer_entries = {
        "sections": {
            "hakijan-tiedot": _get_company_applicants(count=3),
            "paatoksen-toimitus": {
                "sections": {},
                "fields": {
                    "sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen": {
                        "value": True,
                        "extraValue": "",
                    },
                    "postitse-ilmoittamaani-postiosoitteeseen": {
                        "value": True,
                        "extraValue": "",
                    },
                },
            },
        }
    }

    answer_payload = {
        "form": area_search_form.id,
        "area_search": area_search.id,
        "user": user.id,
        "entries": json.dumps(answer_entries),
        "ready": True,
    }

    url = reverse("v1:pub_answer-list")
    response = admin_client.post(url, data=answer_payload)

    return {"answer": response.data, "area_search": area_search}


@pytest.fixture
def answer_email_message():
    email: EmailMessageInput = {
        "subject": "Test email",
        "body": "This is a test email",
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "to": ["test@example.com"],
    }
    return email


@register
class FileScanStatusFactory(factory.django.DjangoModelFactory):
    # Use plotsearch_areasearchattachment as a default content object,
    # because that model might be most relevant to this use case.
    content_object = factory.SubFactory(AreaSearchAttachmentFactory)

    # The remaining required properties can be derived from the referenced object
    @factory.lazy_attribute
    def content_type(self):
        return ContentType.objects.get_for_model(self.content_object)

    @factory.lazy_attribute
    def object_id(self):
        return self.content_object.id

    class Meta:
        model = FileScanStatus


@register
class CollectionLetterFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)
    uploader = factory.SubFactory(UserFactory)

    class Meta:
        model = CollectionLetter


@register
class InfillDevelopmentCompensationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = InfillDevelopmentCompensation


@register
class InfillDevelopmentCompensationLeaseFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)
    infill_development_compensation = factory.SubFactory(
        InfillDevelopmentCompensationFactory
    )

    class Meta:
        model = InfillDevelopmentCompensationLease


@register
class InspectionFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)

    class Meta:
        model = Inspection
