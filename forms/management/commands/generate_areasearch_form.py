from django.core.management.base import BaseCommand

from forms.models.form import Choice, Field, Form, Section


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
        type="radiobuttoninline",
        identifier="hakija",
        enabled=True,
        required=False,
        default_value="1",
    )
    Choice.objects.create(
        field=applicant_field, text="Henkilö", value="2", has_text_input=False
    )
    Choice.objects.create(
        field=applicant_field, text="Yritys/yhteisö", value="1", has_text_input=False
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
        type="textbox",
        identifier="yrityksen-nimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_section,
        label="Y-tunnus",
        type="textbox",
        identifier="y-tunnus",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_section,
        label="Katuosoite",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postinumero",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=3,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postitoimipaikka",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=corporate_section,
        label="Maa",
        type="textbox",
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=5,
        default_value="Suomi",
    )
    Field.objects.create(
        section=corporate_section,
        label="Puhelinnumero",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=corporate_section,
        label="Sähköposti",
        type="textbox",
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
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sukunimi",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sähköposti",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Puhelinnumero",
        type="textbox",
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
        type="checkbox",
        identifier="laskutusosoite-hakija",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=invoice_section,
        label="Verkkolaskuosoite",
        type="textbox",
        identifier="verkkolaskuosoite",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=invoice_section,
        label="Välittäjän tunnus",
        type="textbox",
        identifier="valittajan-tunnus",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section,
        label="Laskutusviite (tulee näkyviin laskulle)",
        type="textbox",
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
        type="checkbox",
        identifier="laskutusosoite-muu",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
        Täytä vain, jos käytössä on muu laskutusosoite.""",
    )
    invoice_section_language = Field.objects.create(
        section=invoice_other_section,
        label="Kieli",
        type="dropdown",
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
        type="textbox",
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Katuosoite",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postinumero",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postitoimipaikka",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Maa",
        type="textbox",
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=6,
        default_value="Suomi",
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Nimi",
        type="textbox",
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Puhelinnumero",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Sähköposti",
        type="textbox",
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
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=people_section,
        label="Sukunimi",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=people_section,
        label="Henkilötunnus",
        type="textbox",
        identifier="henkilotunnus",
        enabled=True,
        required=True,
        sort_order=2,
    )
    people_section_language = Field.objects.create(
        section=people_section,
        label="Kieli",
        type="dropdown",
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
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=people_section,
        label="Sähköposti",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=5,
    )
    Field.objects.create(
        section=people_section,
        label="Katuosoite",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=6,
    )
    Field.objects.create(
        section=people_section,
        label="Postinumero",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=7,
    )
    Field.objects.create(
        section=people_section,
        label="Postitoimipaikka",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=8,
    )
    Field.objects.create(
        section=people_section,
        label="Maa",
        type="textbox",
        identifier="maa",
        enabled=True,
        required=True,
        sort_order=9,
        default_value="Suomi",
    )
    security_ban = Field.objects.create(
        section=people_section,
        label="Turvakielto",
        type="textbox",
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
        field=security_ban,
        text="Kyllä",
        value="kyllä",
        has_text_input=False,
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
        type="checkbox",
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="Täytä vain, jos yhteyshenkilö on eri kuin hakija.",
    )
    Field.objects.create(
        section=contact_section,
        label="Etunimi",
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=contact_section,
        label="Sukunimi",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=contact_section,
        label="Sähköposti",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=contact_section,
        label="Puhelinnumero",
        type="textbox",
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
        type="checkbox",
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
                     Täytä vain, jos laskunsaaja on eri kuin hakija.""",
    )
    invoice_section2_language = Field.objects.create(
        section=invoice_section2,
        label="Kieli",
        type="dropdown",
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
        type="textbox",
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Katuosoite",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postinumero",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postitoimipaikka",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Maa",
        type="textbox",
        identifier="maa",
        enabled=True,
        required=False,
        sort_order=6,
        default_value="Suomi",
    )
    Field.objects.create(
        section=invoice_section2,
        label="Laskutusviite",
        type="textbox",
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Nimi",
        type="textbox",
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Sähköposti",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Puhelinnumero",
        type="textbox",
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
        label="""Vakuutan antamani tiedot oikeiksi.""",
        type="checkbox",
        identifier="vakuutan-antamani-tiedot-oikeiksi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=decision_section,
        label="Vakuutan että hakijat eivät ole pakotteiden kohteena.",
        hint_text="""Vastaamalla KYLLÄ hakija vakuuttaa, että se itse tai yksikään sen suora tai välillinen
            omistaja, vastuuhenkilö tai muu lähellä oleva taho ei ole pakotteiden kohteena tai että
            pakotteita tai varojen jäädyttämispäätöksiä ei ole asetettu hakijalle, hakijan hallinto-, johto-,
            tai valvontaelimen jäsenille tai edustus-, päätös-, määräys- tai valvontavaltaa käyttäville
            henkilöille tai tahoille.""",
        type="checkbox",
        identifier="pakotelista-vakuutus",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=decision_section,
        label="""Hakija suostuu, että Helsingin kaupunki voi antaa päätöksen tai muun asiakirjan tiedoksi
            ilmoittamaani sähköpostiosoitteeseen sähköisenä viestinä.""",
        hint_text="""Päätös tai muu asiakirja lähetetään hakijan yhteyshenkilön sähköpostiositteeseen.
            Mikäli hakijana on yksityishenkilö ja yhteyshenkilöä ei ole ilmoitettu, lähetetään
            päätös tai muu asiakirja hakijan sähköpostiosoitteeseen.""",
        type="checkbox",
        identifier="sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=decision_section,
        label="""Hyväksyn tietojeni tallentamisen ja käsittelyn Helsingin kaupunkiympäristön
            asiakasrekisterin selosteen mukaisesti.""",
        hint_text="Lisätiedot: www.hel.fi/rekisteriseloste",
        type="checkbox",
        identifier="hyvaksyn-tietojeni-tallentamisen",
        enabled=True,
        required=False,
        sort_order=3,
    )

    return form


class Command(BaseCommand):
    help = "Generates an Area Search form."

    def handle(self, *args, **options):
        initialize_area_search_form()
