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
            "MULTIPOLYGON (((24.9277753139783 60.2292931169049, 24.9278229581668 60.2293167737933, 24.9278728789573 60.229339239456, 24.9279249560853 60.2293604597689, 24.9279790640903 60.2293803836078, 24.9279966171371 60.229386420249, 24.9281537999632 60.229405304326, 24.9289596045416 60.2296778530833, 24.9289787792364 60.2296843381706, 24.9288046404959 60.2298116922939, 24.9284129237164 60.2300981608676, 24.9273955680622 60.229795858404, 24.9272729180474 60.2297579798522, 24.9268419512086 60.2296267826066, 24.9264874971251 60.2291634329862, 24.9261350718619 60.2287027159858, 24.9260398266434 60.2285782042873, 24.9266158609816 60.2283899768226, 24.9265668680234 60.2283615446444, 24.9265151292047 60.2283343423552, 24.9264607691697 60.2283084354846, 24.9264039188759 60.2282838864415, 24.9263447152789 60.2282607543635, 24.9262833010022 60.2282390949747, 24.9262198239942 60.2282189604516, 24.9261544371712 60.2282003992972, 24.9260872980493 60.2281834562243, 24.9260185683651 60.2281681720476, 24.9260147520967 60.2281673816872, 24.9259701379458 60.2281588087151, 24.9259247317998 60.2281513348585, 24.9258786430421 60.2281449781218, 24.9258319827 60.2281397538182, 24.925784863178 60.228135674533, 24.9257373979861 60.2281327500933, 24.9256897014674 60.2281309875438, 24.9256418885217 60.2281303911305, 24.9255940743298 60.2281309622903, 24.9255463740748 60.228132699647, 24.9254989026661 60.2281355990156, 24.9254517744614 60.2281396534115, 24.9254051029918 60.2281448530677, 24.9253590006885 60.2281511854583, 24.9253135786114 60.2281586353286, 24.9252689461823 60.2281671847321, 24.9252252109209 60.2281768130733, 24.9252144024076 60.228179392694, 24.9250681299235 60.2282170928083, 24.9249257525414 60.228258317119, 24.9247876132313 60.2283029663261, 24.9246540447581 60.2283509328795, 24.924525368881 60.2284021012378, 24.924401895578 60.2284563481464, 24.9243319306174 60.2284895872242, 24.9242173268501 60.2285484451457, 24.9241086673391 60.2286100289423, 24.9240263659975 60.2286610494062, 24.9239558689153 60.2287331763288, 24.9227708145935 60.2296130979669, 24.9221612368253 60.2300373751509, 24.9220645285224 60.2300914523868, 24.9216834503734 60.2303510737223, 24.9215714249193 60.2303028098852, 24.9214226206379 60.230238699725, 24.9217138839613 60.2300281348717, 24.9217177553545 60.230025183242, 24.9217213308778 60.2300221406919, 24.9217246019174 60.2300190145513, 24.9217275605933 60.2300158123512, 24.9217301997775 60.2300125418063, 24.9217325131125 60.2300092107953, 24.921734495025 60.2300058273432, 24.9217361407407 60.2300023996008, 24.921737446295 60.2299989358261, 24.9217384085427 60.2299954443634, 24.921739025166 60.2299919336241, 24.9217392946792 60.2299884120659, 24.9217392164334 60.2299848881724, 24.921738790617 60.2299813704331, 24.9217380182561 60.2299778673225, 24.9217369012114 60.2299743872799, 24.9217354421741 60.229970938689, 24.9217336446594 60.2299675298578, 24.9217315129974 60.2299641689984, 24.9217290523239 60.2299608642073, 24.9217262685668 60.2299576234462, 24.9217231684326 60.2299544545223, 24.9217217344569 60.2299531108716, 24.9217144558481 60.2299460551453, 24.9217078821219 60.2299388302934, 24.9217020291145 60.2299314537215, 24.9216969109258 60.2299239432004, 24.9216925398858 60.2299163168237, 24.9216889265239 60.2299085929641, 24.9216860795447 60.229900790229, 24.9216840058062 60.2298929274161, 24.9216827103038 60.2298850234676, 24.9216821961578 60.2298770974247, 24.9216824646064 60.2298691683821, 24.9216832729185 60.2298626497526, 24.9209218630555 60.2296144702168, 24.9210073606983 60.2291632121251, 24.921015821732 60.2291185342188, 24.9211030147059 60.2286583456582, 24.921213082359 60.2280775300398, 24.9213028120083 60.2276039407697, 24.9220932936945 60.2276409934401, 24.922765796727 60.2271036365481, 24.9220611224603 60.2268854570948, 24.9224616241098 60.2265654309265, 24.9230490593446 60.2258064021534, 24.9233984512792 60.2254517838185, 24.9234541588221 60.2253952406357, 24.9237912287551 60.2250531168265, 24.9242994049478 60.2245373087923, 24.9245441322871 60.2242888942011, 24.9252855901996 60.2240972749529, 24.9260854071246 60.2238905713526, 24.9274382809783 60.2242100369185, 24.9271287974424 60.2245343556009, 24.9276474784604 60.2246568237787, 24.927687934885 60.2246657781862, 24.9277292258901 60.2246737343537, 24.9277712519989 60.2246806731134, 24.9278139119631 60.2246865777486, 24.9278571030075 60.224691434034, 24.9279007210772 60.2246952302699, 24.9279446610882 60.2246979573104, 24.9279888171811 60.2246996085856, 24.9280330829755 60.2247001801172, 24.928077351827 60.2246996705284, 24.9281215170837 60.2246980810468, 24.9281431232042 60.2246969069186, 24.9283515386152 60.2246843113855, 24.9284061932072 60.2246816842419, 24.92846104111 60.2246803942228, 24.928515950197 60.2246804444356, 24.9285707881938 60.2246818347595, 24.9286254229978 60.2246845618452, 24.9286797229955 60.2246886191232, 24.9287335573799 60.2246939968197, 24.9287867964653 60.2247006819799, 24.9288393120001 60.2247086584997, 24.9288909774754 60.2247179071636, 24.9289416684297 60.224728405692, 24.9289912627487 60.2247401287942, 24.9290396409596 60.2247530482295, 24.9290866865188 60.2247671328751, 24.9291322860926 60.2247823488015, 24.9291763298301 60.2247986593537, 24.9292187116281 60.2248160252397, 24.9292307230967 60.2248212733568, 24.929270788968 60.2248399306425, 24.9293089661998 60.2248595433471, 24.9293272142506 60.2248696346916, 24.93022343598 60.2253775205285, 24.930227038328 60.2253794636129, 24.9302308280136 60.2253813164342, 24.9302347959069 60.2253830745287, 24.9302389324492 60.2253847336611, 24.9302432276749 60.2253862898343, 24.9302476712366 60.2253877392994, 24.9302522524293 60.2253890785645, 24.9302569602164 60.2253903044031, 24.9302617832564 60.225391413862, 24.9302667099302 60.2253924042686, 24.930271728369 60.2253932732367, 24.9302768264828 60.225394018673, 24.9302819919898 60.2253946387816, 24.9302872124457 60.2253951320687, 24.930292475274 60.2253954973458, 24.930297767796 60.225395733733, 24.9303030772615 60.2253958406607, 24.9303083908795 60.2253958178714, 24.9303136958488 60.2253956654201, 24.9303189793894 60.2253953836738, 24.9303242287726 60.2253949733115, 24.9303294313522 60.2253944353217, 24.9303345745946 60.2253937710005, 24.9303396461093 60.2253929819483, 24.9303446336785 60.225392070066, 24.9303495252866 60.2253910375504, 24.9303543091493 60.225389886889, 24.9303589737418 60.2253886208538, 24.9303635078267 60.2253872424947, 24.9303679004809 60.2253857551325, 24.9303721411221 60.2253841623503, 24.9303762195342 60.2253824679853, 24.930380125892 60.2253806761194, 24.9303834056943 60.2253790262418, 24.9309438731481 60.2250846622875, 24.9311492769493 60.2249247606672, 24.9313449058512 60.2250058341877, 24.9314799048349 60.225061780105, 24.9334995943141 60.2260142690243, 24.9337632460662 60.2261386010807, 24.933818351935 60.226164588021, 24.9338157864245 60.2261267869928, 24.9338927483051 60.226109481358, 24.9341019812378 60.2260624333412, 24.9346116804935 60.2259478205358, 24.9380966718863 60.2273153439199, 24.9383702130947 60.2277146432983, 24.9382265882778 60.2282711207616, 24.9381392978166 60.2286093094113, 24.9384032947399 60.2289240805279, 24.9383378519653 60.2290407944473, 24.9382113952431 60.2293030450244, 24.9384889631233 60.2294313681294, 24.938799962067 60.229159950719, 24.9394874223171 60.2293198478512, 24.9396900119737 60.2294841550461, 24.9390948607793 60.2296588803352, 24.9387914632488 60.2297479558305, 24.9383874013375 60.2298665739024, 24.9372095679121 60.2302092575693, 24.9371249463398 60.2302350611558, 24.9370683442711 60.230189152294, 24.9368848107175 60.2300402940762, 24.9356635452658 60.2298767088686, 24.9355825594403 60.2298658605598, 24.934379059859 60.2297046515136, 24.9339948778353 60.2296531874643, 24.9339919064033 60.2295944476404, 24.9339865207418 60.2294879657768, 24.9331467439544 60.2294792162818, 24.9330671109783 60.229477414347, 24.9329877517143 60.2294736711778, 24.9329088573596 60.2294679957925, 24.9328306179914 60.2294604018645, 24.9327532221081 60.2294509076897, 24.9326768561757 60.2294395361419, 24.9326017041784 60.2294263146182, 24.9325279471747 60.2294112749725, 24.9324557628621 60.2293944534391, 24.9323853251477 60.2293758905454, 24.9323208952348 60.2293569051354, 24.9315339726876 60.2291126301885, 24.9325999661542 60.2282630924284, 24.9312079020712 60.2278309845408, 24.9313368581088 60.2277282134113, 24.9299591210016 60.227300521052, 24.9297601184794 60.227238742562, 24.9296930117233 60.2272922199406, 24.9292256570319 60.2276646519495, 24.9284831194396 60.2274341327472, 24.9279177290487 60.2278087376594, 24.9277054735462 60.2278909379512, 24.9275697385973 60.2279969132392, 24.9276458337081 60.228021025773, 24.9274544054548 60.2281704831243, 24.9279408678184 60.228806389578, 24.9282827349743 60.2289220248337, 24.928238466007 60.2289544010617, 24.9277753139783 60.2292931169049), (24.9322140697331 60.2264591835492, 24.932023458066 60.2264031460676, 24.9318386046904 60.2263425237164, 24.9317181912374 60.2262994119744, 24.9304098788808 60.2273291023801, 24.9304741680556 60.2273594041884, 24.9305413692221 60.2273881004526, 24.9306113204842 60.2274151220367, 24.930683853319 60.2274404038389, 24.9307274500755 60.2274543743202, 24.9317178872309 60.2277618261751, 24.9327573873027 60.2266100800325, 24.9322140697331 60.2264591835492)))"  # noqa: E501
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
