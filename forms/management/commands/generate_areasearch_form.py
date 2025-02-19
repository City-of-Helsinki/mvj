from django.core.management.base import BaseCommand

from forms.models.form import Choice, Field, Form, Section


def initialize_area_search_form():
    form = Form.objects.create(
        name="Aluehaun perustietolomake",
        state="ready",
        title="Perustietolomake",
        title_fi="Perustietolomake",
        title_en="Basic information form",
        title_sv="Grundläggande informationsformulär",
        is_area_form=True,
    )
    main_section = Section.objects.create(
        form=form,
        title="Hakijan tiedot",
        title_fi="Hakijan tiedot",
        title_en="Applicant information",
        title_sv="Sökandes uppgifter",
        identifier="hakijan-tiedot",
        visible=True,
        applicant_type="both",
        add_new_allowed=True,
    )
    applicant_field = Field.objects.create(
        section=main_section,
        label="Hakija",
        label_fi="Hakija",
        label_en="Applicant",
        label_sv="Sökande",
        type="radiobuttoninline",
        identifier="hakija",
        enabled=True,
        required=False,
        default_value="1",
    )
    Choice.objects.create(
        field=applicant_field,
        text="Henkilö",
        text_fi="Henkilö",
        text_en="Person",
        text_sv="Person",
        value="2",
        has_text_input=False,
    )
    Choice.objects.create(
        field=applicant_field,
        text="Yritys/yhteisö",
        text_fi="Yritys/yhteisö",
        text_en="Company/organisation",
        text_sv="Företag/organization",
        value="1",
        has_text_input=False,
    )

    corporate_section = Section.objects.create(
        form=form,
        parent=main_section,
        title="Yrityksen tiedot",
        title_fi="Yrityksen tiedot",
        title_en="Company information",
        title_sv="Företagsuppgifter",
        identifier="yrityksen-tiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=corporate_section,
        label="Yrityksen nimi",
        label_fi="Yrityksen nimi",
        label_en="Company name",
        label_sv="Företagsnamn",
        type="textbox",
        identifier="yrityksen-nimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_section,
        label="Y-tunnus",
        label_fi="Y-tunnus",
        label_en="Business ID",
        label_sv="FO-nummer",
        type="textbox",
        identifier="y-tunnus",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_section,
        label="Katuosoite",
        label_fi="Katuosoite",
        label_en="Street address",
        label_sv="Gatuadress",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postinumero",
        label_fi="Postinumero",
        label_en="Postal code",
        label_sv="Postnummer",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=3,
    )
    Field.objects.create(
        section=corporate_section,
        label="Postitoimipaikka",
        label_fi="Postitoimipaikka",
        label_en="City or town",
        label_sv="Postort",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=corporate_section,
        label="Maa",
        label_fi="Maa",
        label_en="Country",
        label_sv="Land",
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
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=6,
    )
    Field.objects.create(
        section=corporate_section,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
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
        title_fi="Yhteyshenkilö",
        title_en="Contact person",
        title_sv="Kontaktperson",
        identifier="yhteyshenkilo-company",
        applicant_type="company",
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Etunimi",
        label_fi="Etunimi",
        label_en="First name",
        label_sv="Förnamn",
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sukunimi",
        label_fi="Sukunimi",
        label_en="Last name",
        label_sv="Efternamn",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=2,
    )
    Field.objects.create(
        section=corporate_contact_section,
        label="Puhelinnumero",
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
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
        title_fi="Laskutustiedot",
        title_en="Billing information",
        title_sv="Faktureringsuppgifter",
        identifier="laskutustiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=invoice_section,
        label="Verkkolaskuosoite",
        label_fi="Verkkolaskuosoite",
        label_en="E-invoice address",
        label_sv="E-fakturaadress",
        type="textbox",
        identifier="verkkolaskuosoite",
        enabled=True,
        required=False,
        sort_order=0,
    )
    Field.objects.create(
        section=invoice_section,
        label="Välittäjän tunnus",
        label_fi="Välittäjän tunnus",
        label_en="Intermediary ID",
        label_sv="Förmedlarens ID",
        type="textbox",
        identifier="valittajan-tunnus",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=invoice_section,
        label="Laskutusviite (tulee näkyviin laskulle)",
        label_fi="Laskutusviite (tulee näkyviin laskulle)",
        label_en="Billing reference (will appear on the invoice)",
        label_sv="Faktureringsreferens (visas på fakturan)",
        type="textbox",
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=2,
    )

    invoice_other_section = Section.objects.create(
        form=form,
        parent=invoice_section,
        title="Muut laskutustiedot",
        title_fi="Muut laskutustiedot",
        title_en="Other billing information",
        title_sv="Övriga faktureringsuppgifter",
        identifier="muut-laskutustiedot",
        visible=True,
        applicant_type="company",
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Muu laskutusosoite",
        label_fi="Muu laskutusosoite",
        label_en="Other billing address",
        label_sv="Annan faktureringsadress",
        type="checkbox",
        identifier="laskutusosoite-muu",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
        Täytä vain, jos käytössä on muu laskutusosoite.""",
        hint_text_fi="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
        Täytä vain, jos käytössä on muu laskutusosoite.""",
        hint_text_en="""Please note that City of Helsinki does not send invoices via email.
        Fill in only if there is another billing address.""",
        hint_text_sv="""Observera att Helsingfors stad inte skickar fakturor via e-post.
        Fyll i endast om det finns en annan faktureringsadress.""",
    )
    invoice_section_language = Field.objects.create(
        section=invoice_other_section,
        label="Kieli",
        label_fi="Kieli",
        label_en="Language",
        label_sv="Språk",
        type="dropdown",
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Choice.objects.create(
        field=invoice_section_language,
        text="suomi",
        text_fi="suomi",
        text_en="Finnish",
        text_sv="finska",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section_language,
        text="ruotsi",
        text_fi="ruotsi",
        text_en="Swedish",
        text_sv="svenska",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section_language,
        text="englanti",
        text_fi="englanti",
        text_en="English",
        text_sv="engelska",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=invoice_other_section,
        label="c/o",
        label_fi="c/o",
        label_en="c/o",
        label_sv="c/o",
        type="textbox",
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Katuosoite",
        label_fi="Katuosoite",
        label_en="Street address",
        label_sv="Gatuadress",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postinumero",
        label_fi="Postinumero",
        label_en="Postal number",
        label_sv="Postnummer",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Postitoimipaikka",
        label_fi="Postitoimipaikka",
        label_en="City or town",
        label_sv="Postort",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Maa",
        label_fi="Maa",
        label_en="Country",
        label_sv="Land",
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
        label_fi="Nimi",
        label_en="Name",
        label_sv="Namn",
        type="textbox",
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Puhelinnumero",
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=invoice_other_section,
        label="Laskutusviite (tulee näkyviin laskulle)",
        label_fi="Laskutusviite (tulee näkyviin laskulle)",
        label_en="Billing reference (will appear on the invoice)",
        label_sv="Faktureringsreferens (visas på fakturan)",
        type="textbox",
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=10,
    )

    people_section = Section.objects.create(
        form=form,
        parent=main_section,
        title="Henkilön tiedot",
        title_fi="Henkilön tiedot",
        title_en="Personal information",
        title_sv="Personuppgifter",
        identifier="henkilon-tiedot",
        visible=True,
        applicant_type="person",
    )
    Field.objects.create(
        section=people_section,
        label="Etunimi",
        label_fi="Etunimi",
        label_en="First name",
        label_sv="Förnamn",
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=people_section,
        label="Sukunimi",
        label_fi="Sukunimi",
        label_en="Last name",
        label_sv="Efternamn",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=True,
        sort_order=1,
    )
    Field.objects.create(
        section=people_section,
        label="Henkilötunnus",
        label_fi="Henkilötunnus",
        label_en="Personal identity code",
        label_sv="Personnummer",
        type="textbox",
        identifier="henkilotunnus",
        enabled=True,
        required=True,
        sort_order=2,
    )
    people_section_language = Field.objects.create(
        section=people_section,
        label="Kieli",
        label_fi="Kieli",
        label_en="Language",
        label_sv="Språk",
        type="dropdown",
        identifier="kieli",
        enabled=True,
        required=True,
        sort_order=3,
    )

    Choice.objects.create(
        field=people_section_language,
        text="suomi",
        text_fi="suomi",
        text_en="Finnish",
        text_sv="finska",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=people_section_language,
        text="ruotsi",
        text_fi="ruotsi",
        text_en="Swedish",
        text_sv="svenska",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=people_section_language,
        text="englanti",
        text_fi="englanti",
        text_en="English",
        text_sv="engelska",
        value="englanti",
        has_text_input=False,
    )

    Field.objects.create(
        section=people_section,
        label="Puhelinnumero",
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=True,
        sort_order=4,
    )
    Field.objects.create(
        section=people_section,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=True,
        sort_order=5,
    )
    Field.objects.create(
        section=people_section,
        label="Katuosoite",
        label_fi="Katuosoite",
        label_en="Street address",
        label_sv="Gatuadress",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=True,
        sort_order=6,
    )
    Field.objects.create(
        section=people_section,
        label="Postinumero",
        label_fi="Postinumero",
        label_en="Postal number",
        label_sv="Postnummer",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=True,
        sort_order=7,
    )
    Field.objects.create(
        section=people_section,
        label="Postitoimipaikka",
        label_fi="Postitoimipaikka",
        label_en="City or town",
        label_sv="Postort",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=True,
        sort_order=8,
    )
    Field.objects.create(
        section=people_section,
        label="Maa",
        label_fi="Maa",
        label_en="Country",
        label_sv="Land",
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
        label_fi="Turvakielto",
        label_en="Non-disclosure for safety reasons",
        label_sv="Spärrmarkering",
        type="textbox",
        identifier="turvakielto",
        enabled=True,
        required=False,
        sort_order=10,
        default_value="ei",
    )
    Choice.objects.create(
        field=security_ban,
        text="Ei",
        text_fi="Ei",
        text_en="No",
        text_sv="Nej",
        value="ei",
        has_text_input=False,
    )
    Choice.objects.create(
        field=security_ban,
        text="Kyllä",
        text_fi="Kyllä",
        text_en="Yes",
        text_sv="Ja",
        value="kyllä",
        has_text_input=False,
    )

    contact_section = Section.objects.create(
        form=form,
        parent=people_section,
        title="Yhteyshenkilö",
        title_fi="Yhteyshenkilö",
        title_en="Contact person",
        title_sv="Kontaktperson",
        identifier="yhteyshenkilo-1",
        applicant_type="person",
    )
    Field.objects.create(
        section=contact_section,
        label="Eri kuin hakija",
        label_fi="Eri kuin hakija",
        label_en="Different from the applicant",
        label_sv="Annan än sökanden",
        type="checkbox",
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="Täytä vain, jos yhteyshenkilö on eri kuin hakija.",
        hint_text_fi="Täytä vain, jos yhteyshenkilö on eri kuin hakija.",
        hint_text_en="Fill in only if the contact person is different from the applicant.",
        hint_text_sv="Fyll i endast om kontaktpersonen är annan än sökanden.",
    )
    Field.objects.create(
        section=contact_section,
        label="Etunimi",
        label_fi="Etunimi",
        label_en="First name",
        label_sv="Förnamn",
        type="textbox",
        identifier="etunimi",
        enabled=True,
        required=False,
        sort_order=1,
    )
    Field.objects.create(
        section=contact_section,
        label="Sukunimi",
        label_fi="Sukunimi",
        label_en="Last name",
        label_sv="Efternamn",
        type="textbox",
        identifier="Sukunimi",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=contact_section,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=contact_section,
        label="Puhelinnumero",
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
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
        title_fi="Laskunsaaja",
        title_en="Invoice recipient",
        title_sv="Fakturamottagare",
        identifier="laskunsaaja",
        applicant_type="person",
    )
    Field.objects.create(
        section=invoice_section2,
        label="Eri kuin hakija",
        label_fi="Eri kuin hakija",
        label_en="Different from the applicant",
        label_sv="Annan än sökanden",
        type="checkbox",
        identifier="eri-kuin-hakija",
        enabled=True,
        required=False,
        sort_order=0,
        hint_text="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
                     Täytä vain, jos laskunsaaja on eri kuin hakija.""",
        hint_text_fi="""Huomaathan, että Helsingin kaupunki ei lähetä laskuja sähköpostitse.
        Täytä vain, jos käytössä on muu laskutusosoite.""",
        hint_text_en="""Please note that City of Helsinki does not send invoices via email.
        Fill in only if there is another billing address.""",
        hint_text_sv="""Observera att Helsingfors stad inte skickar fakturor via e-post.
        Fyll i endast om det finns en annan faktureringsadress.""",
    )
    invoice_section2_language = Field.objects.create(
        section=invoice_section2,
        label="Kieli",
        label_fi="Kieli",
        label_en="Language",
        label_sv="Språk",
        type="dropdown",
        identifier="kieli",
        enabled=True,
        required=False,
        sort_order=1,
    )

    Choice.objects.create(
        field=invoice_section2_language,
        text="suomi",
        text_fi="suomi",
        text_en="Finnish",
        text_sv="finska",
        value="suomi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section2_language,
        text="ruotsi",
        text_fi="ruotsi",
        text_en="Swedish",
        text_sv="svenska",
        value="ruotsi",
        has_text_input=False,
    )
    Choice.objects.create(
        field=invoice_section2_language,
        text="englanti",
        text_fi="englanti",
        text_en="English",
        text_sv="engelska",
        value="englanti",
        has_text_input=False,
    )
    Field.objects.create(
        section=invoice_section2,
        label="c/o",
        label_fi="c/o",
        label_en="c/o",
        label_sv="c/o",
        type="textbox",
        identifier="c_o",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Katuosoite",
        label_fi="Katuosoite",
        label_en="Street address",
        label_sv="Gatuadress",
        type="textbox",
        identifier="katuosoite",
        enabled=True,
        required=False,
        sort_order=3,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postinumero",
        label_fi="Postinumero",
        label_en="Postal number",
        label_sv="Postnummer",
        type="textbox",
        identifier="postinumero",
        enabled=True,
        required=False,
        sort_order=4,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Postitoimipaikka",
        label_fi="Postitoimipaikka",
        label_en="City or town",
        label_sv="Postort",
        type="textbox",
        identifier="postitoimipaikka",
        enabled=True,
        required=False,
        sort_order=5,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Maa",
        label_fi="Maa",
        label_en="Country",
        label_sv="Land",
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
        label_fi="Laskutusviite (tulee näkyviin laskulle)",
        label_en="Billing reference (will appear on the invoice)",
        label_sv="Faktureringsreferens (visas på fakturan)",
        type="textbox",
        identifier="laskutusviite",
        enabled=True,
        required=False,
        sort_order=7,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Nimi",
        label_fi="Nimi",
        label_en="Name",
        label_sv="Namn",
        type="textbox",
        identifier="nimi",
        enabled=True,
        required=False,
        sort_order=8,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Sähköposti",
        label_fi="Sähköposti",
        label_en="Email",
        label_sv="E-post",
        type="textbox",
        identifier="sahkoposti",
        enabled=True,
        required=False,
        sort_order=9,
    )
    Field.objects.create(
        section=invoice_section2,
        label="Puhelinnumero",
        label_fi="Puhelinnumero",
        label_en="Phone number",
        label_sv="Telefonnummer",
        type="textbox",
        identifier="puhelinnumero",
        enabled=True,
        required=False,
        sort_order=10,
    )

    decision_section = Section.objects.create(
        form=form,
        title="Hyväksyn",
        title_fi="Hyväksyn",
        title_en="I agree",
        title_sv="Jag godkänner",
        identifier="päätöksen-toimitus",
    )
    Field.objects.create(
        section=decision_section,
        label="Vakuutan antamani tiedot oikeiksi.",
        label_fi="Vakuutan antamani tiedot oikeiksi.",
        label_en="I certify that the information I have provided is correct",
        label_sv="Jag försäkrar att informationen jag har lämnat är korrekt.",
        type="checkbox",
        identifier="vakuutan-antamani-tiedot-oikeiksi",
        enabled=True,
        required=True,
        sort_order=0,
    )
    Field.objects.create(
        section=decision_section,
        label="Vakuutan että hakijat eivät ole pakotteiden kohteena.",
        label_fi="Vakuutan että hakijat eivät ole pakotteiden kohteena.",
        label_en="I certify that the applicants are not subject to sanctions.",
        label_sv="Jag försäkrar att de sökande inte utsätts för sanktioner",
        hint_text="""Vastaamalla KYLLÄ hakija vakuuttaa, että se itse tai yksikään sen suora tai välillinen
            omistaja, vastuuhenkilö tai muu lähellä oleva taho ei ole pakotteiden kohteena tai että
            pakotteita tai varojen jäädyttämispäätöksiä ei ole asetettu hakijalle, hakijan hallinto-, johto-,
            tai valvontaelimen jäsenille tai edustus-, päätös-, määräys- tai valvontavaltaa käyttäville
            henkilöille tai tahoille.""",
        hint_text_fi="""Vastaamalla KYLLÄ hakija vakuuttaa, että se itse tai
        yksikään sen suora tai välillinen omistaja, vastuuhenkilö tai muu
        lähellä oleva taho ei ole pakotteiden kohteena tai että pakotteita tai
        varojen jäädyttämispäätöksiä ei ole asetettu hakijalle, hakijan
        hallinto-, johto-, tai valvontaelimen jäsenille tai edustus-, päätös-,
        määräys- tai valvontavaltaa käyttäville henkilöille tai tahoille.""",
        hint_text_en="""By answering YES, the applicant certifies that they or
        any of their direct or indirect owners, officers, directors or other
        persons associated with them are not subject to sanctions or that
        sanctions or asset freezing orders have not been imposed on the
        applicant, members of their administrative, management or supervisory
        bodies, or persons or entities with powers of representation, decision
        making, control or supervision.""",
        hint_text_sv="""Genom att svara JA försäkrar den sökande att varken hen
        själv eller en enda direkt eller indirekt ägare, ansvarsperson eller
        annan närvarande aktör utsätts för sanktioner, och att inga sanktioner
        eller beslut om att frysa tillgångar gäller varken den sökande,
        medlemmar i den sökandes förvaltnings-, lednings- eller
        övervakningsorgan eller de personer eller organ som använder sin
        befogenhet att representera, fatta beslut, utfärda bestämmelser eller
        övervaka.""",
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
        label_fi="""Hakija suostuu, että Helsingin kaupunki voi antaa päätöksen
        tai muun asiakirjan tiedoksi ilmoittamaani sähköpostiosoitteeseen
        sähköisenä viestinä.""",
        label_en="""The applicant agrees that the City of Helsinki may deliver
        the decision or other document to the e-mail address I have provided as
        an electronic message.""",
        label_sv="""Den sökande godkänner att Helsingfors stad får ge ett beslut
        eller en annan handling för kännedom i form av ett elektroniskt
        meddelande till den e-postadress som jag har angett.""",
        hint_text="""Päätös tai muu asiakirja lähetetään hakijan yhteyshenkilön sähköpostiositteeseen.
            Mikäli hakijana on yksityishenkilö ja yhteyshenkilöä ei ole ilmoitettu, lähetetään
            päätös tai muu asiakirja hakijan sähköpostiosoitteeseen.""",
        hint_text_fi="""Päätös tai muu asiakirja lähetetään hakijan
        yhteyshenkilön sähköpostiositteeseen.  Mikäli hakijana on
        yksityishenkilö ja yhteyshenkilöä ei ole ilmoitettu, lähetetään päätös
        tai muu asiakirja hakijan sähköpostiosoitteeseen.""",
        hint_text_en="""The decision or other document will be sent to the email
        address of the applicant's contact person. If the applicant is a private
        person and no contact person is indicated, the decision or other
        document will be sent to the applicant's e-mail address.""",
        hint_text_sv="""Beslutet eller handlingen skickas till e-postadressen
        till den sökandes kontaktperson. Om den sökande är en privatperson
        eller ingen kontaktperson har angetts, skickas beslutet eller handlingen
        till den sökandes e-postdress.""",
        type="checkbox",
        identifier="sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen",
        enabled=True,
        required=False,
        sort_order=2,
    )
    Field.objects.create(
        section=decision_section,
        label="""Hyväksyn tietojeni tallentamisen ja käsittelyn sekä
        luottokelpoisuuden ja pakotelistatarkistukset Helsingin
        kaupunkiympäristön asiakasrekisterin selosteen mukaisesti.""",
        label_fi="""Hyväksyn tietojeni tallentamisen ja käsittelyn sekä
        luottokelpoisuuden ja pakotelistatarkistukset Helsingin
        kaupunkiympäristön asiakasrekisterin selosteen mukaisesti.""",
        label_en="""I agree to the storage and processing of my data and the
        creditworthiness and sanctions list checks in accordance with the City
        of Helsinki Urban Environment Division's customer register notice.""",
        label_sv="""Jag godkänner att mina uppgifter lagras och behandlas samt
        kontrollerna av kreditvärdighet och sanktionslistor i enlighet med
        registerbeskrivningen för kundregistret för Helsingfors
        stadsmiljösektor.""",
        hint_text="Olen tutustunut henkilötietojen käsittelyä koskeviin tietosuojaselosteisiin.",
        hint_text_fi="Olen tutustunut henkilötietojen käsittelyä koskeviin tietosuojaselosteisiin.",
        hint_text_en="I have read the data protection notices concerning the processing of personal data.",
        hint_text_sv="Jag har läst integritetspolicyerna angående behandlingen av personuppgifter.",
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
