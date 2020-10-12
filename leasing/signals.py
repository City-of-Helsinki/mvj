from django.db.models.signals import post_delete
from django.dispatch import receiver

from leasing.models import PlotSearchTarget


@receiver(post_delete, sender=PlotSearchTarget)
def post_delete_plan_unit_on_plot_search_target_delete(sender, instance, **kwargs):
    instance.plan_unit.delete()
