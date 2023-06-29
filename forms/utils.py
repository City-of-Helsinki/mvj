from typing import Iterable

from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from rest_framework_gis.filters import InBBoxFilter


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


def _get_plot_search_target_attributes(col, master_row, plot_search_target, worksheet):
    plan_unit = plot_search_target.plan_unit
    custom_detailed_plan = plot_search_target.custom_detailed_plan
    reservation_identifier = (
        plot_search_target.reservation_identifier.identifier.identifier
        if plot_search_target.reservation_identifier is not None
        else "-"
    )

    excel_fields_pls = []

    if plan_unit is not None:
        excel_fields_pls = [
            (_("Identifier"), plan_unit.identifier),
            (_("Area"), plan_unit.area),
            (_("Section area"), plan_unit.section_area),
            (_("Plot division identifier"), plan_unit.plot_division_identifier),
            (
                _("Plot division date of approval"),
                str(plan_unit.plot_division_date_of_approval),
            ),
            (
                _("Plot division effective date"),
                str(plan_unit.plot_division_effective_date),
            ),
            (_("Reservation identifier"), reservation_identifier),
            (_("Plot division state"), plan_unit.plot_division_state.name if plan_unit.plot_division_state is not None else  "-"),
            (_("Detailed plan identifier"), plan_unit.detailed_plan_identifier),
            (
                _("Detailed plan latest processing date"),
                str(plan_unit.detailed_plan_latest_processing_date),
            ),
            (
                _("Detailed plan latest processing date note"),
                plan_unit.detailed_plan_latest_processing_date_note,
            ),
            (_("Plan unit type"), plan_unit.plan_unit_type.name if plan_unit.plan_unit_type is not None else  "-"),
            (_("Plan unit state"), plan_unit.plan_unit_state.name if plan_unit.plan_unit_state is not None else  "-"),
            (_("Plan unit intended use"), plan_unit.plan_unit_intended_use.name if plan_unit.plan_unit_intended_use is not None else  "-"),
            (_("Plan unit status"), plan_unit.plan_unit_status.name),
        ]
    elif custom_detailed_plan is not None:
        excel_fields_pls = [
            (_("Idenfifier"), custom_detailed_plan.identifier),
            (_("Area"), custom_detailed_plan.area),
            (_("Section area"), custom_detailed_plan.lease_area.section_area),
            (_("Plot division identifier"), "-"),
            (_("Plot division date of approval"), "-"),
            (_("Plot division effective date"), "-"),
            (_("Reservation identifier"), reservation_identifier),
            (_("Plot division state"), "-"),
            (_("Detailed plan identifier"), custom_detailed_plan.detailed_plan),
            (
                _("Detailed plan latest processing date"),
                str(custom_detailed_plan.detailed_plan_latest_processing_date),
            ),
            (
                _("Detailed plan latest processing date note"),
                custom_detailed_plan.detailed_plan_latest_processing_date_note,
            ),
            (_("Plan unit type"), custom_detailed_plan.type.name),
            (_("Plan unit state"), custom_detailed_plan.state.name),
            (_("Plan unit intended use"), custom_detailed_plan.intended_use.name),
            (_("Plan unit status"), "-"),
        ]

    for excel_field in excel_fields_pls:
        if master_row == 0:
            worksheet.write(master_row, col, excel_field[0])
        worksheet.write(master_row + 1, col, excel_field[1])
        col += 1

    worksheet.write(master_row + 1, col, plot_search_target.target_type.name)

    return col


def _write_entry_value(col, entry, field, row, worksheet):
    if field.type.identifier == "checkbox":
        choices = entry.value.strip("][").split(", ")
        try:
            choices = [int(choice) for choice in choices]
            from forms.models import Choice

            worksheet.write(
                row + 1,
                col,
                str(
                    [
                        choice.value
                        for choice in Choice.objects.filter(id__in=choices)
                    ]
                ),
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
    if entry_rows - master_row > 1:
        for pre_row in range(master_row, entry_rows):
            entry_col = 0
            entry_col = _write_plot_search_info(entry_col, pre_row, target_status.plot_search_target.plot_search, worksheet)
            _get_plot_search_target_attributes(entry_col, pre_row, target_status.plot_search_target, worksheet)
    return worksheet, col, entry_rows - master_row


def get_answer_worksheet(
    target_status, worksheet, master_row, with_target_statuses=True
):
    col = 0

    plot_search_target = target_status.plot_search_target

    form = target_status.plot_search_target.plot_search.form

    plot_search = plot_search_target.plot_search

    col = _write_plot_search_info(col, master_row, plot_search, worksheet)

    col = _get_plot_search_target_attributes(col, master_row, plot_search_target, worksheet)

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
            worksheet.write(master_row, col, _("Share of rental"))
            worksheet.write(master_row, col + 1, _("Reserved"))
            worksheet.write(master_row, col + 2, _("Added target to applicant"))
            worksheet.write(master_row, col + 3, _("Counsel date"))
            worksheet.write(master_row, col + 4, _("Decline reason"))
            worksheet.write(master_row, col + 5, _("Reservation conditions"))
            worksheet.write(master_row, col + 6, _("Proposed management"))
            worksheet.write(master_row, col + 7, _("Arguments"))

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


def _write_plot_search_info(col, master_row, plot_search, worksheet):
    excel_fields = [
        (_("Name"), plot_search.name),
        (_("Type"), plot_search.subtype.plot_search_type.name),
        (_("Subtype"), plot_search.subtype.name),
        (_("Begin at"), plot_search.begin_at.isoformat("T")),
        (_("End at"), plot_search.end_at.isoformat("T")),
        (_("Search class"), plot_search.search_class),
        (_("Stage"), plot_search.stage.name),
    ]
    for excel_field in excel_fields:
        if master_row == 0:
            worksheet.write(master_row, col, excel_field[0])
        worksheet.write(master_row + 1, col, excel_field[1])
        col += 1
    return col


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
        worksheet, col, entry_rows = _get_subsection_field_entries(
            worksheet,
            subsection,
            master_row,
            col,
            area_search,
            last_applicant_section,
        )

    return worksheet, col, entry_rows - master_row


def get_area_search_answer_worksheet(
    area_search, worksheet, master_row
):
    col = 0

    form = area_search.answer.form

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
        (_("Preparer"), "{} {}".format(area_search.preparer.first_name, area_search.preparer.last_name)),
        (_("Decline reason"), area_search.area_search_status.decline_reason),
        (_("Preparer note"), area_search.area_search_status.preparer_note),
        (_("Status notes"), ",".join(
            [status_note.note for status_note in area_search.area_search_status.status_notes.all()]
        )),
    ]

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
