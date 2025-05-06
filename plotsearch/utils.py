from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from forms.enums import ApplicantType
from leasing.enums import ServiceUnitId
from plotsearch.enums import AreaSearchLessor
from utils.email import EmailMessageInput, send_email

if TYPE_CHECKING:
    from plotsearch.models import AreaSearch, AreaSearchIntendedUse


def map_intended_use_to_lessor(
    intended_use: "AreaSearchIntendedUse",
) -> AreaSearchLessor | None:
    """Maps AreaSearchIntendedUse to AreaSearchLessor."""
    intended_uses_with_lessors = {
        "ravitsemus, myynti ja mainonta": AreaSearchLessor.AKV,
        "taide ja kulttuuri": AreaSearchLessor.AKV,
        "varastointi ja jakelu": AreaSearchLessor.AKV,
        "työmaat": AreaSearchLessor.AKV,
        "muu alueen käyttö": AreaSearchLessor.MAKE,
        "veneily ja laiturit": AreaSearchLessor.UPA,
        "urheilu ja liikunta": AreaSearchLessor.LIPA,
    }
    try:
        lessor = intended_uses_with_lessors.get(intended_use.name_fi.lower(), None)
    except AttributeError:
        return None

    return lessor


def map_lessor_enum_to_service_unit_id(lessor: AreaSearchLessor) -> int:
    """Maps AreaSearchLessor to service unit ID."""
    lessor_to_service_unit_id = {
        AreaSearchLessor.MAKE: int(ServiceUnitId.MAKE),
        AreaSearchLessor.AKV: int(ServiceUnitId.AKV),
        AreaSearchLessor.LIPA: int(ServiceUnitId.KUVA_LIPA),
        AreaSearchLessor.UPA: int(ServiceUnitId.KUVA_UPA),
        AreaSearchLessor.NUP: int(ServiceUnitId.KUVA_NUP),
    }
    return lessor_to_service_unit_id[lessor]


def map_intended_use_to_service_unit_id(intended_use: "AreaSearchIntendedUse") -> int:
    """Maps AreaSearchIntendedUse to service unit ID."""
    lessor = map_intended_use_to_lessor(intended_use)
    if not lessor:
        raise ValueError(f"Invalid intended use name_fi with ID {intended_use.pk}")
    return map_lessor_enum_to_service_unit_id(lessor)


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
        ).format(
            receiver=receiver,
            url=url,
            covering_note=covering_note,
        )
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


def send_areasearch_lessor_changed_email(
    area_search: "AreaSearch",
    new_lessor: AreaSearchLessor,
    old_lessor: AreaSearchLessor,
    language: str = "fi",
) -> None:
    """
    Sends an email to lessors when area search lessor changes.
    """
    with override(language):
        from_email = settings.FROM_EMAIL_AREA_SEARCH or settings.MVJ_EMAIL_FROM
        to_addresses = [
            _get_lessor_email_to_address(new_lessor),
            _get_lessor_email_to_address(old_lessor),
        ]
        email_input: EmailMessageInput = {
            "from_email": from_email,
            "to": to_addresses,
            "subject": _get_areasearch_lessor_changed_email_subject(area_search),
            "body": _get_areasearch_lessor_changed_email_body(
                area_search, new_lessor, old_lessor
            ),
            "attachments": [],
        }
        send_email(email_input)


def _get_lessor_email_to_address(lessor: AreaSearchLessor) -> str:
    """
    Returns email address of the lessor contact.

    Raises:
        ValueError when email address cannot be found.
    """
    from leasing.models import Contact

    if lessor is None:
        raise ValueError("Lessor is None. Cannot send email.")

    service_unit_id = map_lessor_enum_to_service_unit_id(lessor)
    try:
        service_unit_contact = Contact.objects.get(
            is_lessor=True,
            service_unit_id=service_unit_id,
        )
        if service_unit_contact.email:
            return service_unit_contact.email
        else:
            raise ValueError(
                f"Contact with service unit ID {service_unit_id} does not have an email address. Cannot send email."
            )
    except Contact.DoesNotExist:
        raise ValueError(
            f"Lessor contact with service unit ID {service_unit_id} not found. Cannot send email."
        )
    except Contact.MultipleObjectsReturned:
        raise ValueError(
            f"Multiple lessor contacts with service unit ID {service_unit_id} found. Cannot send email."
        )


def _get_areasearch_lessor_changed_email_subject(
    area_search: "AreaSearch",
) -> str:
    if area_search is None:
        raise ValueError("Area search is None. Cannot generate email subject.")

    answer = area_search.answer
    if answer is None:
        raise ValueError("Answer is None. Cannot generate email subject.")

    identifier = area_search.identifier or "<tunnus puuttuu>"
    district = area_search.district or "<kaupunginosa puuttuu>"
    address = (
        area_search.address or "<osoite puuttuu>"
    )  # Ideally "if many addresses, the one from the first property code",
    # but areasearch address field is calculated elsewhere from geometry.

    applicants = []
    get_applicant(answer, applicants)
    applicant = applicants[0] if applicants else "<hakija puuttuu>"

    date_format = "%d.%m.%Y"
    start_date = (
        area_search.start_date.strftime(date_format) if area_search.start_date else "-"
    )
    end_date = (
        area_search.end_date.strftime(date_format) if area_search.end_date else "-"
    )

    return f"Muutos Aluehakemus {identifier} {district} {address} {applicant} alkaa {start_date} - päättyy {end_date}"


def _get_areasearch_lessor_changed_email_body(
    area_search: "AreaSearch",
    new_lessor: AreaSearchLessor,
    old_lessor: AreaSearchLessor,
) -> str:
    if area_search is None:
        raise ValueError("Area search is None. Cannot generate email body.")

    identifier = area_search.identifier or "<tunnus puuttuu>"
    intended_use = area_search.intended_use or "-"
    intended_use_description = area_search.description_intended_use or "-"
    return f"""Aluehakemuksen {identifier} uusi vuokranantaja on {new_lessor}, oli {old_lessor}.
Käyttötarkoitus: {intended_use}
Tarkempi kuvaus käyttötarkoituksesta: {intended_use_description}"""
