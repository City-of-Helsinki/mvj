from django import template

register = template.Library()


@register.filter
def filter_answer(qs, answer):
    return qs.filter(entry_section__answer=answer)


@register.filter
def filter_only_parent(qs):
    return qs.filter(parent__isnull=True)


@register.simple_tag
def get_applicant(entry_section):
    first_name = entry_section.entries.filter(
        field__identifier="etunimi",
        field__section__identifier="henkilon-tiedot",
    ).first()

    if first_name is None:
        name = (
            entry_section.entries.filter(field__identifier="yrityksen-nimi")
            .first()
            .value
        )
    else:
        name = "{} {}".format(
            first_name.value,
            entry_section.entries.filter(
                field__identifier="Sukunimi",
                field__section__identifier="henkilon-tiedot",
            )
            .first()
            .value,
        )

    return name


@register.filter
def filter_applicant(qs, applicant_identifier):
    if applicant_identifier is None:
        return qs

    entries = []
    for entry in qs:
        if entry.entry_section.metadata["identifier"] == applicant_identifier:
            entries.append(entry)

    return entries


@register.filter
def filter_plot_search_target(qs, plot_search_target):
    """Exclude entries in section 'haettava-kohde' where `plot_search_target` does not match metadata."""
    if plot_search_target is None:
        return qs

    entries = []
    for entry in qs:
        if not (
            "haettava-kohde" in entry.entry_section.identifier
            and entry.entry_section.metadata.get("identifier") != plot_search_target.id
        ):
            # Skip entries that are not the target, otherwise multiple targets are shown
            entries.append(entry)

    return entries
