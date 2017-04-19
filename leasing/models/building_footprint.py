from django.db import models
from django.utils.translation import ugettext_lazy as _

from .application import Application


class BuildingFootprint(models.Model):
    application = models.ForeignKey(Application, related_name="building_footprints", on_delete=models.CASCADE)
    use = models.CharField(verbose_name=_("Use"), null=True, blank=True, max_length=2048)
    area = models.IntegerField(verbose_name=_("Area in full square meters"), null=True, blank=True)
