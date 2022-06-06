from django.conf import settings
from django.contrib.gis.db import models as gmodels
from django.db import models
from django.utils import timezone
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField
from rest_framework.serializers import ValidationError

from forms.models import Answer, Form
from forms.models.form import EntrySection
from leasing.enums import PlotSearchTargetType
from leasing.models import Decision, PlanUnit
from leasing.models.mixins import NameModel, TimeStampedSafeDeleteModel
from plotsearch.enums import InformationCheckName, InformationState, SearchClass
from users.models import User


class PlotSearchType(NameModel):
    """
    In Finnish: Hakutyyppi
    """

    ordering = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search type")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search types")
        ordering = ["ordering", "name"]


class PlotSearchSubtype(NameModel):
    """
    In Finnish: Haun alatyyppi
    """

    plot_search_type = models.ForeignKey(PlotSearchType, on_delete=models.CASCADE)
    show_district = models.BooleanField(default=False)
    ordering = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search subtype")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search subtypes")
        ordering = ["ordering", "name"]


class PlotSearchStage(NameModel):
    """
    In Finnish: Haun vaihe
    """

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Plot search stage")
        verbose_name_plural = pgettext_lazy("Model name", "Plot search stages")


class PlotSearch(TimeStampedSafeDeleteModel, NameModel):
    """
    In Finnish: Tonttihaku
    """

    # In Finnish: Valmistelija
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Haun tyyppi
    subtype = models.ForeignKey(
        PlotSearchSubtype,
        verbose_name=_("Subtype"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Alkuaika
    begin_at = models.DateTimeField(verbose_name=_("Begin at"), null=True, blank=True)

    # In Finnish: Loppuaika
    end_at = models.DateTimeField(verbose_name=_("End at"), null=True, blank=True)

    # In Finnish: Haun luokittelu
    search_class = EnumField(enum=SearchClass, max_length=30, null=True, blank=True)

    # In Finnish: Haun vaihe
    stage = models.ForeignKey(
        PlotSearchStage,
        verbose_name=_("Stage"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Haettavat kohteet, menettelyvaraus ja suoravaraus
    targets = models.ManyToManyField(PlanUnit, through="PlotSearchTarget")

    # In Finnish: Lomake
    form = models.OneToOneField(Form, on_delete=models.SET_NULL, null=True)

    decisions = models.ManyToManyField(
        Decision, related_name="plot_searches", blank=True
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Plot search")
        verbose_name_plural = pgettext_lazy("Model name", "Plot searches")

    def __str__(self):
        return "Plot search #{}".format(self.id)


class PlotSearchTarget(models.Model):
    """
    In Finnish: Tonttihaun kohde
    """

    # In Finnish: Tonttihaku
    plot_search = models.ForeignKey(
        PlotSearch, on_delete=models.CASCADE, related_name="plot_search_targets"
    )

    # In Finnish: Kaavayksikkö
    plan_unit = models.OneToOneField(PlanUnit, on_delete=models.CASCADE)

    # In finnish: Hakemukset
    answers = models.ManyToManyField(
        Answer, related_name="targets", blank=True, through="ApplicationStatus"
    )

    # In Finnish: Tonttihaun kohteet: Haettavat kohteet, menettelyvaraus ja suoravaraus
    target_type = EnumField(
        PlotSearchTargetType, verbose_name=_("Target type"), max_length=30,
    )

    def save(self, *args, **kwargs):
        self.clean()
        return super(PlotSearchTarget, self).save(*args, **kwargs)

    def clean(self):
        if self.target_type != PlotSearchTargetType.SEARCHABLE:
            return

        if self.plot_search.begin_at is not None:
            if timezone.now() < self.plot_search.begin_at:
                return

        plot_search = PlotSearch.objects.get(pk=self.plot_search.pk)
        if plot_search.form is None:
            pls = PlotSearchTarget.objects.filter(pk=self.pk).first()
            for field in self._meta.fields:
                if pls is None:
                    break
                if getattr(self, field.name) != getattr(pls, field.name):
                    raise ValidationError(
                        code="no_adding_searchable_targets_after_begins_at"
                    )
            for field in self.plot_search._meta.fields:
                if field.name != "form" and getattr(self, field.name) != getattr(
                    plot_search, field.name
                ):
                    raise ValidationError(
                        code="no_adding_searchable_targets_after_begins_at"
                    )
            return

        raise ValidationError(code="no_adding_searchable_targets_after_begins_at")


class InformationCheck(models.Model):
    """
    In Finnish: Lisätiedon tila
    """

    # In Finnish: Nimi
    name = EnumField(enum=InformationCheckName, max_length=30)

    # In Finnish: Käsittelijä
    preparer = models.ForeignKey(
        User,
        verbose_name=_("Preparer"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Vastauksen osio
    entry_section = models.ForeignKey(EntrySection, on_delete=models.PROTECT)

    # In Finnish: Tila
    state = EnumField(
        enum=InformationState, max_length=30, default=InformationState.NOT_CHECKED
    )

    # In Finnish: Kommentti
    comment = models.TextField(null=True, blank=True)


class ApplicationStatus(models.Model):
    plot_search_target = models.ForeignKey(
        PlotSearchTarget, related_name="statuses", blank=True, on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        Answer, related_name="statuses", on_delete=models.CASCADE
    )

    reserved = models.BooleanField(default=False)


class TargetInfoLink(models.Model):
    """
    In Finnish: Lisätietolinkki
    """

    # In Finnish: Tonttihaun kohde
    plot_search_target = models.ForeignKey(
        PlotSearchTarget, on_delete=models.CASCADE, related_name="info_links"
    )

    # In Finnish: Lisätietolinkki
    url = models.URLField()

    # In Finnish: Lisätietolinkkiteksti
    description = models.CharField(max_length=255)

    # In Finnish: Kieli
    language = models.CharField(max_length=255, choices=settings.LANGUAGES)


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True)


class FavouriteTarget(models.Model):
    favourite = models.ForeignKey(
        Favourite, on_delete=models.CASCADE, related_name="targets"
    )
    plot_search_target = models.ForeignKey(PlotSearchTarget, on_delete=models.CASCADE)


class IntendedUse(NameModel):
    # In Finnish: Käyttötarkoitus

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Area search intended use")
        verbose_name_plural = pgettext_lazy("Model name", "Area search intended uses")
        ordering = ["name"]


class IntendedSubUse(NameModel):
    # In finnish: Käyttötarkoituksen alitarkoitus

    intended_use = models.ForeignKey(IntendedUse, on_delete=models.CASCADE)

    class Meta(NameModel.Meta):
        verbose_name = pgettext_lazy("Model name", "Area search sub intended use")
        verbose_name_plural = pgettext_lazy(
            "Model name", "Area search sub intended uses"
        )
        ordering = ["intended_use", "name"]


class AreaSearch(models.Model):
    # In Finnish: aluehaku

    geometry = gmodels.MultiPolygonField(
        srid=4326, verbose_name=_("Geometry"), null=True, blank=True
    )

    description_area = models.TextField()

    intended_use = models.ForeignKey(IntendedSubUse, on_delete=models.CASCADE)
    description_intended_use = models.TextField()

    start_date = models.DateTimeField(verbose_name=_("Begin at"), null=True, blank=True)
    end_date = models.DateTimeField(verbose_name=_("End at"), null=True, blank=True)

    form = models.OneToOneField(
        Form, on_delete=models.SET_NULL, null=True, related_name="area_search"
    )


from plotsearch.signals import *  # noqa: E402 F403 F401
