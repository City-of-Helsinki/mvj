from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from plotsearch.models import PlotSearchTarget


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
