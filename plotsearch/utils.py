from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from forms.enums import ApplicantType
from plotsearch.enums import AreaSearchLessor


def map_intended_use_to_lessor(intended_use):
    # Keeping these for a transformation period
    old_intended_uses_with_lessors = {
        "myynti- ja mainontapaikat": AreaSearchLessor.AKV,
        "taide- ja kulttuuripaikat": AreaSearchLessor.AKV,
        "varasto- ja jakelualueet": AreaSearchLessor.AKV,
        "työmaa tukikohdat ja alueet": AreaSearchLessor.AKV,
        "veneily ja laiturialueet": AreaSearchLessor.KUVA,
        "urheilu- ja liikuntapaikat": AreaSearchLessor.KUVA,
    }
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
        lessor = {**intended_uses_with_lessors, **old_intended_uses_with_lessors}.get(
            intended_use.name.lower(), None
        )
    except AttributeError:
        return None

    return lessor


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
