from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from forms.models.form import EntrySection
from plotsearch.enums import InformationCheckName
from plotsearch.models import InformationCheck, PlotSearch, PlotSearchTarget


@receiver(pre_save, sender=PlotSearchTarget)
def prepare_plan_unit_on_plot_search_target_save(sender, instance, **kwargs):
    plan_unit = instance.plan_unit

    if plan_unit is None:
        return
    if plan_unit.is_master:
        plan_unit.pk = None
        plan_unit.is_master = False
        usage_permissions = plan_unit.usage_distributions.all()
        plan_unit.save()

        for usage_permission in usage_permissions:
            usage_permission.pk = None
            usage_permission.plan_unit = plan_unit
            usage_permission.save()

        instance.plan_unit = plan_unit


@receiver(post_delete, sender=PlotSearchTarget)
def post_delete_plan_unit_on_plot_search_target_delete(sender, instance, **kwargs):
    plan_unit = instance.plan_unit
    if plan_unit is None:
        return
    plan_unit.usage_distributions.all().delete()
    plan_unit.delete()


@receiver(pre_save, sender=PlotSearch)
def prepare_template_form_on_plot_search_save(sender, instance, **kwargs):
    form = instance.form

    if instance.id:
        previous_form = PlotSearch.objects.get(pk=instance.id).form
        if (
            instance.form
            and previous_form is not None
            and instance.form.id != previous_form.id
        ):
            previous_form.delete()

    if form is None:
        return

    if form.is_template:
        cloned_form = form.clone()
        cloned_form.is_template = False
        cloned_form.save()
        instance.form = cloned_form


@receiver(post_save, sender=EntrySection)
def create_information_checks_on_answer_save(sender, instance, **kwargs):
    if "hakijan-tiedot" in instance.identifier:
        for entry in InformationCheckName.choices():
            InformationCheck.objects.create(
                name=entry[0], preparer=None, entry_section=instance, comment=None
            )
