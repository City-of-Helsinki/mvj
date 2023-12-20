import logging
from io import BytesIO
from smtplib import (
    SMTPDataError,
    SMTPException,
    SMTPRecipientsRefused,
    SMTPSenderRefused,
)
from typing import Iterable, List, Tuple, TypedDict, Union

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils.translation import override
from django.utils.translation import ugettext as _
from django_q.tasks import Conf, async_task
from django_xhtml2pdf.utils import generate_pdf
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter

from forms.enums import AnswerType

logger = logging.getLogger(__name__)


def generate_unique_identifier(klass, field_name, field_value, max_length, **kwargs):
    origin_identifier = slugify(field_value)[:max_length]
    unique_identifier = origin_identifier

    filter_var = {field_name: unique_identifier}
    filter_ext = kwargs.get("filter")
    filter_var.update(filter_ext)

    index = 1
    while klass.objects.filter(**filter_var).exists():
        unique_identifier = "{}-{}".format(
            origin_identifier[: max_length - len(str(index)) - 1], index
        )
        filter_var.update({field_name: unique_identifier})
        index += 1
    return unique_identifier


def clone_object(obj, attrs={}):

    # we start by building a "flat" clone
    clone = obj._meta.model.objects.get(id=obj.id)
    clone.id = None

    # if caller specified some attributes to be overridden, use them
    for key, value in attrs.items():
        setattr(clone, key, value)

    # save the partial clone to have a valid ID assigned
    clone.save()

    # Scan field to further investigate relations
    fields = clone._meta.get_fields()
    for field in fields:

        # Manage M2M fields by replicating all related records found on parent "obj" into "clone"
        if not field.auto_created and field.many_to_many:
            for row in getattr(obj, field.name).all():
                getattr(clone, field.name).add(row)

        # Manage 1-N and 1-1 relations by cloning child objects
        if not (field.auto_created and field.is_relation):
            continue
        if field.many_to_many or field.name == "parent":
            # do nothing
            continue
        elif field.name == "subsections":
            attrs = {field.remote_field.name: clone, "form": clone.form}
            children = field.related_model.objects.filter(
                **{field.remote_field.name: obj}
            )

        else:
            # provide "clone" object to replace "obj" on remote field
            attrs = {field.remote_field.name: clone}
            if "parent" in (x.name for x in field.related_model._meta.get_fields()):
                children = field.related_model.objects.filter(
                    parent__isnull=True, **{field.remote_field.name: obj}
                )
            else:
                children = field.related_model.objects.filter(
                    **{field.remote_field.name: obj}
                )

        for child in children:
            clone_object(child, attrs)

    return clone


def _get_plot_search_target_attributes(plot_search_target):
    plan_unit = plot_search_target.plan_unit
    custom_detailed_plan = plot_search_target.custom_detailed_plan
    reservation_identifier = (
        plot_search_target.reservation_identifier.identifier.identifier
        if plot_search_target.reservation_identifier is not None
        else "-"
    )

    if plan_unit is not None:
        return [
            ("Identifier", plan_unit.identifier),
            ("Area", plan_unit.area),
            ("Section area", plan_unit.section_area),
            ("Plot division identifier", plan_unit.plot_division_identifier),
            (
                "Plot division date of approval",
                plan_unit.plot_division_date_of_approval.isoformat(),
            ),
            (
                "Plot division effective date",
                plan_unit.plot_division_effective_date.isoformat(),
            ),
            ("Reservation identifier", reservation_identifier),
            ("Plot division state", plan_unit.plot_division_state.name),
            ("Detailed plan identifier", plan_unit.detailed_plan_identifier),
            (
                "Detailed plan latest processing date",
                str(plan_unit.detailed_plan_latest_processing_date),
            ),
            (
                "Detailed plan latest processing date note",
                plan_unit.detailed_plan_latest_processing_date_note,
            ),
            ("Plan unit type", plan_unit.plan_unit_type.name),
            ("Plan unit state", plan_unit.plan_unit_state.name),
            ("Plan unit intended use", plan_unit.plan_unit_intended_use.name),
            ("Plan unit status", plan_unit.plan_unit_status.name),
        ]
    elif custom_detailed_plan is not None:
        return [
            ("Idenfifier", custom_detailed_plan.identifier),
            ("Area", custom_detailed_plan.area),
            ("Section area", custom_detailed_plan.lease_area.section_area),
            ("Plot division identifier", "-"),
            ("Plot division date of approval", "-"),
            ("Plot division effective date", "-"),
            ("Reservation identifier", reservation_identifier),
            ("Plot division state", "-"),
            ("Detailed plan identifier", custom_detailed_plan.detailed_plan),
            (
                "Detailed plan latest processing date",
                str(custom_detailed_plan.detailed_plan_latest_processing_date),
            ),
            (
                "Detailed plan latest processing date note",
                custom_detailed_plan.detailed_plan_latest_processing_date_note,
            ),
            ("Plan unit type", custom_detailed_plan.type.name),
            ("Plan unit state", custom_detailed_plan.state.name),
            ("Plan unit intended use", custom_detailed_plan.intended_use.name),
            ("Plan unit status", "-"),
        ]


def _write_entry_value(col, entry, field, row, worksheet):
    if field.type.identifier == "checkbox":
        choices = entry.value.strip("][").split(", ")
        try:
            choices = [int(choice) for choice in choices]
            from forms.models import Choice

            worksheet.write(
                row + 1,
                col,
                str([choice.value for choice in Choice.objects.filter(id__in=choices)]),
            )
        except ValueError:
            worksheet.write(row + 1, col, "")
    else:
        worksheet.write(row + 1, col, entry.value)


def _get_subsection_field_entries(  # noqa: C901
    worksheet,
    section,
    master_row,
    col,
    target_status,
    last_applicant_section,
    entry_rows=0,
):
    for field in section.fields.all():
        row = master_row
        if master_row == 0:
            worksheet.write(
                master_row, col, "{} - {}".format(field.section.title, field.label)
            )
        for entry in field.entry_set.filter(
            entry_section__answer__statuses__in=[target_status,],  # noqa: E231
        ):
            _write_entry_value(col, entry, field, row, worksheet)

            row += 1
        entry_rows = row if entry_rows < row else entry_rows
        col += 1

    if section == last_applicant_section:
        for row in range(master_row, entry_rows):
            from plotsearch.models import InformationCheck

            for information_check in InformationCheck.objects.filter(
                entry_section__identifier="hakijan-tiiedot[{}]".format(
                    row - master_row
                ),
                entry_section__answer=target_status.answer,
            ):
                if master_row == 0:
                    worksheet.write(master_row, col, information_check.name)
                worksheet.write(master_row + 1, col, information_check.state)
                col += 1

    for subsection in section.subsections.all():
        worksheet, col, entry_rows = _get_subsection_field_entries(
            worksheet,
            subsection,
            master_row,
            col,
            target_status,
            last_applicant_section,
        )

    return worksheet, col, entry_rows - master_row


def _get_area_subsection_field_entries(  # noqa: C901
    worksheet,
    section,
    master_row,
    col,
    area_search,
    last_applicant_section,
    entry_rows=0,
):
    for field in section.fields.all():
        row = master_row
        if master_row == 0:
            worksheet.write(
                master_row, col, "{} - {}".format(field.section.title, field.label)
            )
        for entry in field.entry_set.filter(
            entry_section__answer__area_search=area_search,  # noqa: E231
        ):
            _write_entry_value(col, entry, field, row, worksheet)

            row += 1
        entry_rows = row if entry_rows < row else entry_rows
        col += 1

    if section == last_applicant_section:
        for row in range(master_row, entry_rows):
            from plotsearch.models import InformationCheck

            for information_check in InformationCheck.objects.filter(
                entry_section__identifier="hakijan-tiiedot[{}]".format(
                    row - master_row
                ),
                entry_section__answer=area_search.answer,
            ):
                if master_row == 0:
                    worksheet.write(master_row, col, information_check.name)
                worksheet.write(master_row + 1, col, information_check.state)
                col += 1

    for subsection in section.subsections.all():
        worksheet, col, entry_rows = _get_area_subsection_field_entries(
            worksheet, subsection, master_row, col, area_search, last_applicant_section,
        )

    return worksheet, col, entry_rows - master_row


def get_answer_worksheet(
    target_status, worksheet, master_row, with_target_statuses=True
):
    col = 0

    plot_search_target = target_status.plot_search_target

    form = target_status.plot_search_target.plot_search.form

    plot_search = plot_search_target.plot_search

    excel_fields = [
        ("Name", plot_search.name),
        ("Type", plot_search.subtype.plot_search_type.name),
        ("Subtype", plot_search.subtype.name),
        ("Begin at", plot_search.begin_at.isoformat("T")),
        ("End at", plot_search.end_at.isoformat("T")),
        ("Search class", plot_search.search_class),
        ("Stage", plot_search.stage.name),
    ]

    for excel_field in excel_fields:
        if master_row == 0:
            worksheet.write(master_row, col, excel_field[0])
        worksheet.write(master_row + 1, col, excel_field[1])
        col += 1

    excel_fields_pls = _get_plot_search_target_attributes(plot_search_target)

    for excel_field in excel_fields_pls:
        if master_row == 0:
            worksheet.write(master_row, col, excel_field[0])
        worksheet.write(master_row + 1, col, excel_field[1])
        col += 1

    worksheet.write(master_row + 1, col, plot_search_target.target_type.name)

    from forms.models import Section

    last_applicant_section = Section.objects.filter(
        form=form, parent__identifier="hakijan-tiedot"
    ).last()

    for section in form.sections.all():
        worksheet, col, entry_rows = _get_subsection_field_entries(
            worksheet, section, master_row, col, target_status, last_applicant_section
        )

    if with_target_statuses:
        if isinstance(target_status.reservation_conditions, Iterable):
            conditions = ", ".join(target_status.reservation_conditions)
        else:
            conditions = target_status.reservation_conditions

        if master_row == 0:
            worksheet.write(master_row, col, "Share of rental")
            worksheet.write(master_row, col + 1, "Reserved")
            worksheet.write(master_row, col + 2, "Added target to applicant")
            worksheet.write(master_row, col + 3, "Counsel date")
            worksheet.write(master_row, col + 4, "Decline reason")
            worksheet.write(master_row, col + 5, "Reservation conditions")
            worksheet.write(master_row, col + 6, "Proposed management")
            worksheet.write(master_row, col + 7, "Arguments")

        worksheet.write(
            master_row + 1,
            col,
            "{} / {}".format(
                target_status.share_of_rental_indicator,
                target_status.share_of_rental_denominator,
            ),
        )
        worksheet.write(master_row + 1, col + 1, target_status.reserved)
        worksheet.write(
            master_row + 1, col + 2, target_status.added_target_to_applicant
        )
        worksheet.write(master_row + 1, col + 3, str(target_status.counsel_date))
        worksheet.write(master_row + 1, col + 4, target_status.decline_reason)
        worksheet.write(master_row + 1, col + 5, conditions)
        worksheet.write(
            master_row + 1,
            col + 6,
            ", ".join(
                [
                    "{} {} {}".format(
                        management.proposed_financing.name,
                        management.proposed_management.name,
                        management.hitas.name,
                    )
                    for management in target_status.proposed_managements.all()
                ]
            ),
        )
        worksheet.write(master_row + 1, col + 7, target_status.arguments)

    master_row += entry_rows

    return worksheet, master_row


def _get_answer_search_subsection_field_entries(  # noqa: C901
    worksheet,
    section,
    master_row,
    col,
    area_search,
    last_applicant_section,
    entry_rows=0,
):
    for field in section.fields.all():
        row = master_row
        if master_row == 0:
            worksheet.write(
                master_row, col, "{} - {}".format(field.section.title, field.label)
            )
        for entry in field.entry_set.filter(
            entry_section__answer__area_search=area_search,  # noqa: E231
        ):
            _write_entry_value(col, entry, field, row, worksheet)

            row += 1
        entry_rows = row if entry_rows < row else entry_rows
        col += 1

    if section == last_applicant_section:
        for row in range(master_row, entry_rows):
            from plotsearch.models import InformationCheck

            for information_check in InformationCheck.objects.filter(
                entry_section__identifier="hakijan-tiedot[{}]".format(row - master_row),
                entry_section__answer=area_search.answer,
            ):
                if master_row == 0:
                    worksheet.write(master_row, col, information_check.name)
                worksheet.write(master_row + 1, col, information_check.state)
                col += 1

    for subsection in section.subsections.all():
        worksheet, col, entry_rows = _get_answer_search_subsection_field_entries(
            worksheet, subsection, master_row, col, area_search, last_applicant_section,
        )

    return worksheet, col, entry_rows - master_row


def get_area_search_answer_worksheet(area_search, worksheet, master_row):
    col = 0

    form = area_search.answer.form

    preparer = "-"
    if area_search.preparer is not None:
        preparer = "{} {}".format(
            area_search.preparer.first_name, area_search.preparer.last_name
        )

    area_search_status = area_search.area_search_status

    excel_fields = [
        (_("Lessor"), area_search.lessor.value),
        (_("Description area"), area_search.description_area),
        (_("Address"), area_search.address),
        (_("District"), area_search.district),
        (_("Intended use"), area_search.intended_use.name),
        (_("Description intended use"), area_search.description_intended_use),
        (_("Start date"), area_search.start_date.isoformat("T")),
        (_("End date"), area_search.end_date.isoformat("T")),
        (_("Received date"), area_search.received_date.isoformat("T")),
        (_("Identifier"), area_search.identifier),
        (_("State"), area_search.state.value),
        (_("Preparer"), preparer),
    ]

    if area_search_status is not None:
        excel_fields.append((_("Decline reason"), area_search_status.decline_reason)),
        excel_fields.append((_("Preparer note"), area_search_status.preparer_note)),
        excel_fields.append(
            (
                _("Status notes"),
                ",".join(
                    [
                        status_note.note
                        for status_note in area_search.area_search_status.status_notes.all()
                    ]
                ),
            )
        )

    for excel_field in excel_fields:
        if master_row == 0:
            worksheet.write(master_row, col, excel_field[0])
        worksheet.write(master_row + 1, col, excel_field[1])
        col += 1

    from forms.models import Section

    last_applicant_section = Section.objects.filter(
        form=form, parent__identifier="hakijan-tiedot"
    ).last()

    for section in form.sections.all():
        worksheet, col, entry_rows = _get_answer_search_subsection_field_entries(
            worksheet, section, master_row, col, area_search, last_applicant_section
        )

    master_row += 1

    return worksheet, master_row


class AnswerInBBoxFilter(InBBoxFilter):
    def filter_queryset(self, request, queryset, view):
        filter_fields = [
            "targets__plan_unit__geometry",
            "targets__custom_detailed_plan__lease_area__geometry",
        ]
        include_overlapping = getattr(view, "bbox_filter_include_overlapping", False)
        if include_overlapping:
            geo_django_filter = "bboverlaps"
        else:
            geo_django_filter = "contained"

        bbox = self.get_filter_bbox(request)
        if not bbox:
            return queryset
        return queryset.filter(
            Q(**{"%s__%s" % (filter_fields[0], geo_django_filter): bbox})
            | Q(**{"%s__%s" % (filter_fields[1], geo_django_filter): bbox})
        ).distinct("pk")


def handle_email_sending(response: Response, user_language: str) -> None:
    answer_id = response.data.get("id")
    input_data: AnswerInputData = {
        "answer_id": answer_id,
        "answer_type": None,
        "user_language": user_language,
    }
    area_search_id = response.data.get("area_search")
    if area_search_id:
        input_data["answer_type"] = AnswerType.AREA_SEARCH

    target_statuses = response.data.get("target_statuses")
    if target_statuses:
        input_data["answer_type"] = AnswerType.TARGET_STATUS

    if not area_search_id and not target_statuses:
        logging.error(
            (
                "Could not send email of answer creation: "
                f"Neither area_search or target_statuses found in answer: {answer_id}"
            )
        )
        return response

    async_task(
        generate_and_queue_answer_emails, input_data=input_data, timeout=Conf.TIMEOUT,
    )


class AnswerInputData(TypedDict):
    answer_id: int
    answer_type: AnswerType
    user_language: str  # ISO 639-1 language code, e.g. "fi", "en", "sv"


class EmailMessageInput(TypedDict):
    from_email: str
    to: List[str]
    subject: str
    body: str
    attachments: List[Tuple[str, Union[bytes, BytesIO], str]]


def _get_email_to_addresses(answer) -> List[str]:
    from forms.models.form import Entry

    # The query intends to find email addresses for applicants that are either
    # a company ("yrityksen-tiedot") or a private person ("henkilon-tiedot")
    # or a private persons contact person ("henkilon-tiedot[0].yhteyshenkilo").
    # Duplicates are removed with distinct("value").
    email_entries = (
        Entry.objects.filter(
            entry_section__answer=answer, field__identifier="sahkoposti"
        )
        .exclude(path__icontains="laskutustiedot",)
        .exclude(path__icontains="laskunsaaja",)
        .exclude(value__isnull=True,)
        .exclude(value="")
        .distinct("value")
        .values_list("value", flat=True)
    )
    email_addresses = list(email_entries)
    return email_addresses


def _generate_target_status_email(answer) -> EmailMessageInput:
    from plotsearch.utils import build_pdf_context

    context: dict = {}
    attachments: List[Tuple[str, bytes, str]] = []
    target_statuses = getattr(answer, "statuses", None)
    target_status_identifiers = ", ".join(
        target_statuses.values_list("application_identifier", flat=True)
    )
    context.update(target_status_identifiers=target_status_identifiers)
    from_email = settings.FROM_EMAIL_PLOT_SEARCH
    email_subject = _(f"Copy of plot application(s) {target_status_identifiers}")
    email_body = render_to_string("target_status/email_detail.txt", context)

    for target_status in target_statuses.all():
        context["object"] = target_status
        context = build_pdf_context(context)
        pdf: BytesIO = generate_pdf("target_status/detail.html", context=context)
        email_pdf: bytes = pdf.getvalue()
        attachment_filename = f"{target_status.application_identifier}.pdf"
        attachments.append([attachment_filename, email_pdf, "application/pdf"])

    email_message: EmailMessageInput = {
        "from_email": from_email or settings.MVJ_EMAIL_FROM,
        "to": _get_email_to_addresses(answer),
        "subject": email_subject,
        "body": email_body,
        "attachments": attachments,
    }

    return email_message


def _generate_area_search_email(answer) -> EmailMessageInput:
    from plotsearch.utils import build_pdf_context

    context: dict = {}
    attachments: List[Tuple[str, bytes, str]] = []
    area_search = getattr(answer, "area_search", None)
    context["object"] = area_search
    context = build_pdf_context(context)
    from_email = settings.FROM_EMAIL_AREA_SEARCH
    email_subject = _(f"Copy of area rental application {area_search.identifier}")
    email_body = render_to_string("area_search/email_detail.txt", context)
    pdf: BytesIO = generate_pdf("area_search/detail.html", context=context)
    email_pdf: bytes = pdf.getvalue()
    attachment_filename = f"{getattr(area_search, 'identifier', email_subject)}.pdf"
    attachments.append([attachment_filename, email_pdf, "application/pdf"])

    email_message: EmailMessageInput = {
        "from_email": from_email or settings.MVJ_EMAIL_FROM,
        "to": _get_email_to_addresses(answer),
        "subject": email_subject,
        "body": email_body,
        "attachments": attachments,
    }

    return email_message


def _generate_plotsearch_email(answer_type: AnswerType, answer) -> EmailMessageInput:
    if answer_type == AnswerType.AREA_SEARCH:
        return _generate_area_search_email(answer)
    elif answer_type == AnswerType.TARGET_STATUS:
        return _generate_target_status_email(answer)
    raise ValueError(f"Answer type {answer_type} not supported.")


def generate_and_queue_answer_emails(input_data: AnswerInputData) -> None:
    from forms.models import Answer

    answer_id = input_data.get("answer_id")
    answer_type = input_data.get("answer_type")
    user_preferred_language = input_data.get("user_language", "fi")
    user_language = (
        user_preferred_language
        if user_preferred_language in get_supported_language_codes()
        else "fi"
    )

    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        logger.error(
            f"Answer with id {answer_id} does not exist, unable to generate emails."
        )
        return

    # Set the translation language to user's preferred language
    # The language selection comes from the users browser
    with override(user_language):
        email_message_input = _generate_plotsearch_email(answer_type, answer)

    send_answer_email(email_message_input)

    return


def send_answer_email(email_message_input: EmailMessageInput) -> None:
    if hasattr(settings, "DEBUG") and settings.DEBUG is True:
        logging.info("Not sending email in debug mode.")
        logging.info(f"Email message: {email_message_input}")
        return

    email_message = EmailMessage(**email_message_input)

    try:
        email_message.send()
    except SMTPSenderRefused:
        logging.exception(
            "Server refused sender address when sending email. Abandoning retrying."
        )
        return  # No point retrying
    except SMTPRecipientsRefused:
        logging.exception(
            "Server refused recipient address when sending email. Abandoning retrying."
        )
        return  # No point retrying
    except (SMTPDataError, SMTPException) as e:
        logging.exception(
            f"Server responded with unexpected error code when sending email: {e}"
        )
        raise e
    except TimeoutError as e:
        logging.exception("Server connection timed out when sending email.")
        raise e


def get_supported_language_codes() -> List[str]:
    """Gets language codes allowed to be translated to."""
    return [language_code for language_code, _language_name in settings.LANGUAGES]
