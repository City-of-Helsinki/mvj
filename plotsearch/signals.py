from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from forms.models import Form
from plotsearch.models import PlotSearch, PlotSearchTarget


@receiver(pre_save, sender=PlotSearchTarget)
def prepare_plan_unit_on_plot_search_target_save(sender, instance, **kwargs):
    plan_unit = instance.plan_unit
    if plan_unit.is_master:
        plan_unit.pk = None
        plan_unit.is_master = False
        plan_unit.save()
        instance.plan_unit = plan_unit


@receiver(post_delete, sender=PlotSearchTarget)
def post_delete_plan_unit_on_plot_search_target_delete(sender, instance, **kwargs):
    instance.plan_unit.delete()


@receiver(pre_save, sender=PlotSearch)
def prepare_template_form_on_plot_search_save(sender, instance, **kwargs):
    form = instance.form

    if instance.id:
        previous_form = PlotSearch.objects.get(pk=instance.id).form
        if instance.form and instance.form.id != previous_form.id:
            previous_form.delete()

    if form.is_template:
        cloned_form = form.clone()
        cloned_form.is_template = False
        cloned_form.save()
        instance.form = cloned_form

