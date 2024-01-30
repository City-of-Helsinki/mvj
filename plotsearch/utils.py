from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from forms.enums import ApplicantType
from forms.models import Choice, Field, FieldType, Form, Section
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


def _get_field_type(identifier, default_id=None):
    try:
        field_type = FieldType.objects.get(identifier=identifier)
    except FieldType.DoesNotExist:
        return default_id
    return field_type.id


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
    field_type_field_ids = {
        "textbox": _get_field_type("textbox", 1),
        "textarea": _get_field_type("textarea", 2),
        "dropdown": _get_field_type("dropdown", 3),
        "checkbox": _get_field_type("checkbox", 4),
        "radiobutton": _get_field_type("radiobutton", 5),
        "radiobuttoninline": _get_field_type("radiobuttoninline", 6),
        "uploadfiles": _get_field_type("uploadfiles", 7),
        "fractional": _get_field_type("fractional", 8),
    }
    applicant_field = Field.objects.create(
        section=main_section,
        label="Hakija",
        type_id=field_type_field_ids.get("radiobuttoninline"),
        identifier="hakija",
        enabled=True,
        required=False,
        default_value="2",
    )
    Choice.objects.create(
        field=applicant_field, text="Henkilö", value="2", has_text_input=False
    )
    Choice.objects.create(
        field=applicant_field, text="Yritys", value="1", has_text_input=False
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
        type_id=field_type_field_ids.get("textbox"),
        identifier="yrityksen-nimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_section,
        label="Y-tunnus",
        type_id=field_type_field_ids.get("textbox"),
        identifier="y-tunnus",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_section,
        label="Katuosoite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postinumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=3,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postitoimipaikka",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=corporate_section,
        label="Maa",
        type_id=field_type_field_ids.get("textbox"),
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=5,
        default_value="Suomi",
    )
    Field.objects.create(
        section=corporate_section,
        label="Puhelinnumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=corporate_section,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=7,
    )

    corporate_contact_section = Section.objects.create(
        form=form,
        parent=corporate_section,
        title="Yhteyshenkilö",
        identifier="yhteyshenkilo-company",
        applicant_type="company",
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Etunimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sukunimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Puhelinnumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=True,
        sort_order=3,
    )

    invoice_section = Section.objects.create(
        form=form,
        parent=corporate_contact_section,
        title="Laskutustiedot",
        identifier="laskutustiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=invoice_section,
        label="Hakijan laskutusosoite",
        type_id=field_type_field_ids.get("checkbox"),
        identifier="laskutusosoite-hakija",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=invoice_section,
        label="Verkkolaskuosoite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="verkkolaskuosoite",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=invoice_section,
        label="Välittäjän tunnus",
        type_id=field_type_field_ids.get("textbox"),
        identifier="valittajan-tunnus",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section,
        label="Laskutusviite (tulee näkyviin laskulle)",
        type_id=field_type_field_ids.get("textbox"),
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=3,
    )

    invoice_other_section = Section.objects.create(
        form=form,
        parent=invoice_section,
        title="Muut laskutustiedot",
        identifier="muut-laskutustiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Muu laskutusosoite",
        type_id=field_type_field_ids.get("checkbox"),
        identifier="laskutusosoite-muu",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="Täytä vain, jos käytössä on muu laskutusosoite.",
    )
    invoice_section_language = Field.objects.create(
        section=invoice_other_section,
        label="Kieli",
        type_id=field_type_field_ids.get("dropdown"),
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=1,
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
        section=invoice_other_section,
        label="c/o",
        type_id=field_type_field_ids.get("textbox"),
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Katuosoite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postinumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postitoimipaikka",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Maa",
        type_id=field_type_field_ids.get("textbox"),
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=6,
        default_value="Suomi",
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Nimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Puhelinnumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=9,
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
        type_id=field_type_field_ids.get("textbox"),
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=people_section,
        label="Sukunimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=people_section,
        label="Henkilötunnus",
        type_id=field_type_field_ids.get("textbox"),
        identifier="henkilotunnus",
        enabled=True,
        required=True,
        sort_order=2,
    )
    people_section_language = Field.objects.create(
        section=people_section,
        label="Kieli",
        type_id=field_type_field_ids.get("dropdown"),
        identifier="kieli",
        enabled=True,
        required=True,
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
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=people_section,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=5,
    )
    Field.objects.create(
        section=people_section,
        label="Katuosoite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=6,
    )
    Field.objects.create(
        section=people_section,
        label="Postinumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=7,
    )
    Field.objects.create(
        section=people_section,
        label="Postitoimipaikka",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=8,
    )
    Field.objects.create(
        section=people_section,
        label="Maa",
        type_id=field_type_field_ids.get("textbox"),
        identifier="maa",
        enabled=True,
        required=True,
        sort_order=9,
        default_value="Suomi",
    )
    security_ban = Field.objects.create(
        section=people_section,
        label="Turvakielto",
        type_id=field_type_field_ids.get("textbox"),
        identifier="turvakielto",
        enabled=True,
        required=False,
        sort_order=10,
        default_value="ei",
    )
    Choice.objects.create(
        field=security_ban, text="Ei", value="ei", has_text_input=False
    )
    Choice.objects.create(
        field=security_ban, text="Kyllä", value="kyllä", has_text_input=False,
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
        type_id=field_type_field_ids.get("checkbox"),
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="Täytä vain, jos yhteyshenkilö on eri kuin hakija.",
    )
    Field.objects.create(
        section=contact_section,
        label="Etunimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=contact_section,
        label="Sukunimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=contact_section,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=contact_section,
        label="Puhelinnumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=4,
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
        type_id=field_type_field_ids.get("checkbox"),
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse. Täytä vain, jos laskunsaaja on eri kuin hakija.",
    )
    invoice_section2_language = Field.objects.create(
        section=invoice_section2,
        label="Kieli",
        type_id=field_type_field_ids.get("dropdown"),
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=1,
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
        label="c/o",
        type_id=field_type_field_ids.get("textbox"),
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Katuosoite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postinumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postitoimipaika",
        type_id=field_type_field_ids.get("textbox"),
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Maa",
        type_id=field_type_field_ids.get("textbox"),
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=6,
        default_value="Suomi",
    )
    Field.objects.create(
        section=invoice_section2,
        label="Laskutusviite",
        type_id=field_type_field_ids.get("textbox"),
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Nimi",
        type_id=field_type_field_ids.get("textbox"),
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Sähköposti",
        type_id=field_type_field_ids.get("textbox"),
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Puhelinnumero",
        type_id=field_type_field_ids.get("textbox"),
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=10,
    )

    decision_section = Section.objects.create(
        form=form, title="Päätöksen toimitus", identifier="päätöksen-toimitus"
    )
    Field.objects.create(
        section=decision_section,
        label="Hakija suostuu, että Helsingin kaupunki voi antaa päätöksen tai muun asiakirjan tiedoksi ilmoittamaani sähköpostiosoitteeseen sähköisenä viestinä.",
        hint_text="Päätös tai muu asiakirja lähetetään hakijan yhteyshenkilön sähköpostiositteeseen. Mikäli hakijana on yksityishenkilö ja yhteyshenkilöä ei ole ilmoitettu, lähetetään päätös tai muu asiakirja hakijan sähköpostiosoitteeseen.",
        type_id=field_type_field_ids.get("checkbox"),
        identifier="sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=decision_section,
        label="Hyväksyn tietojeni tallentamisen ja käsittelyn Helsingin kaupunkiympäristön asiakasrekisterin selosteen mukaisesti. Lisätiedot: www.hel.fi/rekisteriseloste",
        type_id=field_type_field_ids.get("checkbox"),
        identifier="hyvaksyn-tietojeni-tallentamisen",
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


def build_pdf_context(context):
    applicants = []

    applicant_entry_sections = context["object"].answer.entry_sections.filter(
        entries__field__identifier="hakija",
        entries__field__section__identifier="hakijan-tiedot",
    )
    for applicant_entry_section in applicant_entry_sections:
        applicants.append(
            {
                "entry_section": applicant_entry_section,
                "identifier": applicant_entry_section.metadata["identifier"],
                "section": context["object"].answer.form.sections.get(
                    form__id=context["object"].answer.form_id,
                    identifier="hakijan-tiedot",
                ),
                "applicant_type": get_applicant_type(
                    applicant_entry_section.entries.get(
                        field__identifier="hakija",
                        field__section__identifier="hakijan-tiedot",
                    ).value
                ),
            }
        )

    context.update(
        applicants=applicants,
        other_sections=context["object"].answer.form.sections.exclude(
            identifier="hakijan-tiedot"
        ),
    )
    return context


def get_applicant_type(applicant_type):
    if applicant_type == "2":
        return ApplicantType.PERSON
    if applicant_type == "1":
        return ApplicantType.COMPANY
    return ApplicantType.BOTH
