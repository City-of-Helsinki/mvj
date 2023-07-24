from django.utils.translation import override
from django.utils.translation import ugettext_lazy as _

from forms.models import Choice, Field, Form, Section
from plotsearch.enums import AreaSearchLessor


def map_intended_use_to_lessor(intended_use):
    if intended_use is None:
        return None

    akv_list = [
        "myynti- ja mainontapaikat",
        "taide- ja kulttuuripaikat",
        "varasto- ja jakelualueet",
        "työmaa tukikohdat ja alueet",
    ]
    make_list = ["muu alueen käyttö"]
    kuva_list = ["veneily ja laiturialueet", "urheilu- ja liikuntapaikat"]

    if intended_use.name.lower() in akv_list:
        return AreaSearchLessor.AKV
    elif intended_use.name.lower() in make_list:
        return AreaSearchLessor.MAKE
    elif intended_use.name.lower() in kuva_list:
        return AreaSearchLessor.KUVA

    return None


def initialize_area_search_form():
    form = Form.objects.create(
        name="Aluehaun perustietolomake",
        state="ready",
        title="Perustietolomake",
        is_area_form=True,
    )
    main_section = Section.objects.create(
        form=form,
        title="Hakijan tiedot",
        identifier="hakijan-tiedot",
        visible=True,
        applicant_type="both",
        add_new_allowed=True,
    )
    applicant_field = Field.objects.create(
        section=main_section,
        label="Hakija",
        type_id=6,
        identifier="hakija",
        enabled=True,
        required=False,
        default_value="1",
    )
    Choice.objects.create(
        field=applicant_field, text="Yritys", value="1", has_text_input=False
    )
    Choice.objects.create(
        field=applicant_field, text="Henkilö", value="2", has_text_input=False
    )

    corporate_section = Section.objects.create(
        form=form,
        parent=main_section,
        title="Yrityksen tiedot",
        identifier="yrityksen-tiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=corporate_section,
        label="Yrityksen nimi",
        type_id=1,
        identifier="yrityksen-nimi",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_section,
        label="Y-tunnus",
        type_id=1,
        identifier="y-tunnus",
        enabled=True,
        required=False,
        sort_order=1,
    )
    corporate_section_language = Field.objects.create(
        section=corporate_section,
        label="Kieli",
        type_id=3,
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=2,
    )

    Choice.objects.create(
        field=corporate_section_language,
        text="suomi",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=corporate_section_language,
        text="ruotsi",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=corporate_section_language,
        text="englanti",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=corporate_section,
        label="Puhelinnumero",
        type_id=1,
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=corporate_section,
        label="Sähköposti",
        type_id=1,
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=corporate_section,
        label="Katuosoite",
        type_id=1,
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postinumero",
        type_id=1,
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postitoimipaikka",
        type_id=1,
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=corporate_section,
        label="Maa, jos ei Suomi",
        type_id=1,
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=corporate_section,
        label="Hallintaosuus",
        type_id=8,
        identifier="hallintaosuus",
        enabled=True,
        required=False,
        sort_order=9,
    )

    invoice_section = Section.objects.create(
        form=form,
        parent=corporate_section,
        title="Laskutustiedot",
        identifier="laskutustiedot",
        visible=True,
        applicant_type="company",
    )
    invoice_section_language = Field.objects.create(
        section=invoice_section,
        label="Kieli",
        type_id=3,
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=0,
    )

    Choice.objects.create(
        field=invoice_section_language,
        text="suomi",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section_language,
        text="ruotsi",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section_language,
        text="englanti",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=invoice_section,
        label="Puhelinnumero",
        type_id=1,
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=invoice_section,
        label="Sähköposti",
        type_id=1,
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section,
        label="Katuosoite",
        type_id=1,
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_section,
        label="Maa, jos ei Suomi",
        type_id=1,
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_section,
        label="Postitoimipaikka",
        type_id=1,
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_section,
        label="Postinumero",
        type_id=1,
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=6,
    )

    reference_section = Section.objects.create(
        form=form,
        parent=invoice_section,
        title="Laskutusviite",
        identifier="laskutusviite-1",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=reference_section,
        label="Verkkolaskutusosoite",
        type_id=1,
        identifier="verkkolaskutusosoite",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=reference_section,
        label="Laskutusviite",
        type_id=1,
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=1,
    )

    people_section = Section.objects.create(
        form=form,
        parent=main_section,
        title="Henkilön tiedot",
        identifier="henkilon-tiedot",
        visible=True,
        applicant_type="person",
    )
    Field.objects.create(
        section=people_section,
        label="Etunimi",
        type_id=1,
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=people_section,
        label="Sukunimi",
        type_id=1,
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=people_section,
        label="Henkilötunnus",
        type_id=1,
        identifier="henkilotunnus",
        enabled=True,
        required=False,
        sort_order=2,
    )
    people_section_language = Field.objects.create(
        section=people_section,
        label="Kieli",
        type_id=3,
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=3,
    )

    Choice.objects.create(
        field=people_section_language, text="suomi", value="suomi", has_text_input=False
    )
    Choice.objects.create(
        field=people_section_language,
        text="ruotsi",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=people_section_language,
        text="englanti",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=people_section,
        label="Puhelinnumero",
        type_id=1,
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=people_section,
        label="Sähköposti",
        type_id=1,
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=people_section,
        label="Katuosoite",
        type_id=1,
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=people_section,
        label="Postinumero",
        type_id=1,
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=people_section,
        label="Kaupunki",
        type_id=1,
        identifier="kaupunki",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=people_section,
        label="Maa, jos ei Suomi",
        type_id=1,
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=people_section,
        label="Turvakielto",
        type_id=1,
        identifier="turvakielto",
        enabled=True,
        required=False,
        sort_order=10,
    )
    Field.objects.create(
        section=people_section,
        label="Hallintaosuus",
        type_id=8,
        identifier="hallintaosuus",
        enabled=True,
        required=False,
        sort_order=11,
    )

    contact_section = Section.objects.create(
        form=form,
        parent=people_section,
        title="Yhteyshenkilö",
        identifier="yhteyshenkilo-1",
        applicant_type="person",
    )
    Field.objects.create(
        section=contact_section,
        label="Eri kuin hakija",
        type_id=4,
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=contact_section,
        label="Etunimi",
        type_id=1,
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=contact_section,
        label="Sukunimi",
        type_id=1,
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=contact_section,
        label="Henkilötunnus",
        type_id=1,
        identifier="henkilotunnus",
        enabled=True,
        required=False,
        sort_order=3,
    )
    contact_person_language = Field.objects.create(
        section=contact_section,
        label="Kieli",
        type_id=3,
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=4,
    )

    Choice.objects.create(
        field=contact_person_language, text="suomi", value="suomi", has_text_input=False
    )
    Choice.objects.create(
        field=contact_person_language,
        text="ruotsi",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=contact_person_language,
        text="englanti",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=contact_section,
        label="Puhelinnumero",
        type_id=1,
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=contact_section,
        label="Sähköposti",
        type_id=1,
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=contact_section,
        label="Katuosoite",
        type_id=1,
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=contact_section,
        label="Postinumero",
        type_id=1,
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=contact_section,
        label="Postitoimipaika",
        type_id=1,
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=contact_section,
        label="Maa, jos ei Suomi",
        type_id=1,
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=10,
    )

    invoice_section2 = Section.objects.create(
        form=form,
        parent=people_section,
        title="Laskunsaaja",
        identifier="laskunsaaja",
        applicant_type="person",
    )
    Field.objects.create(
        section=invoice_section2,
        label="Eri kuin hakija",
        type_id=4,
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Etunimi",
        type_id=1,
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Sukunimi",
        type_id=1,
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Henkilötunnus",
        type_id=1,
        identifier="henkilotunnus",
        enabled=True,
        required=False,
        sort_order=3,
    )
    invoice_section2_language = Field.objects.create(
        section=invoice_section2,
        label="Kieli",
        type_id=3,
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=4,
    )

    Choice.objects.create(
        field=invoice_section2_language,
        text="suomi",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section2_language,
        text="ruotsi",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section2_language,
        text="englanti",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=invoice_section2,
        label="Puhelinnumero",
        type_id=1,
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Sähköposti",
        type_id=1,
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Katuosoite",
        type_id=1,
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postinumero",
        type_id=1,
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postitoimipaika",
        type_id=1,
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Maa, jos ei Suomi",
        type_id=1,
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=10,
    )

    reference_section2 = Section.objects.create(
        form=form,
        parent=invoice_section2,
        title="Laskutusviite",
        identifier="laskutusviite",
        applicant_type="person",
    )
    Field.objects.create(
        section=reference_section2,
        label="Laskutusviite",
        type_id=1,
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=0,
    )

    decision_section = Section.objects.create(
        form=form, title="Päätöksen toimitus", identifier="päätöksen-toimitus"
    )
    Field.objects.create(
        section=decision_section,
        label="Sähköisesti ilmoittamaani sähköpostiosoitteeseen",
        type_id=4,
        identifier="sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=decision_section,
        label="Postitse ilmoittamaani postiosoitteeseen",
        type_id=4,
        identifier="postitse-ilmoittamaani-postiosoitteeseen",
        enabled=True,
        required=False,
        sort_order=1,
    )

    return form


def get_applicant(answer, reservation_recipients):
    applicant_sections = answer.entry_sections.filter(
        entries__field__identifier="hakija",
        entries__field__section__identifier="hakijan-tiedot",
    )
    for applicant_section in applicant_sections:
        applicant_type = applicant_section.entries.get(
            field__identifier="hakija", field__section__identifier="hakijan-tiedot"
        ).value
        if applicant_type == "1":
            applicants = applicant_section.entries.filter(
                field__identifier="yrityksen-nimi",
                field__section__identifier="yrityksen-tiedot",
            )
            for applicant in applicants:
                reservation_recipients.append(applicant.value)
        elif applicant_type == "2":
            front_names = applicant_section.entries.filter(
                field__identifier="etunimi",
                field__section__identifier="henkilon-tiedot",
            ).order_by("entry_section")
            last_names = applicant_section.entries.filter(
                field__identifier="Sukunimi",
                field__section__identifier="henkilon-tiedot",
            ).order_by("entry_section")
            for idx, front_name in enumerate(front_names):
                last_name = last_names[idx]
                reservation_recipients.append(
                    " ".join([front_name.value, last_name.value])
                )


def compose_direct_reservation_mail_subject(language):
    with override(language):
        subject = _("You have received a link for a direct reservation plot search")
    return subject


def compose_direct_reservation_mail_body(
    first_name, last_name, company, url, covering_note, language
):
    with override(language):
        receiver = (
            company
            if company
            else "{first_name} {last_name}".format(
                first_name=first_name, last_name=last_name
            )
        )
        body = _(
            "Hi {receiver}! Here is the link for the direct reservation plot search: {url} \n\n{covering_note}"
        ).format(receiver=receiver, url=url, covering_note=covering_note,)
    return body


def pop_default(validated_data, index, default_value):
    try:
        return validated_data.pop(index)
    except IndexError:
        return default_value
