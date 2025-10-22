from decimal import ROUND_HALF_UP, Decimal

from auditlog.registry import auditlog
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class VatManager(models.Manager):
    def get_for_date(self, the_date=None):
        """Returns the VAT for the date"""
        if the_date is None:
            the_date = timezone.now().date()

        return (
            self.get_queryset()
            .filter(start_date__lte=the_date)
            .filter(Q(end_date__gte=the_date) | Q(end_date__isnull=True))
            .order_by("-start_date")
            .first()
        )


class Vat(models.Model):
    """Value added tax

    In Finnish: ALV (Arvonlisävero)
    """

    # In Finnish: Prosentti
    percent = models.DecimalField(
        verbose_name=_("Percent"),
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # In Finnish: Alkupäivämäärä
    start_date = models.DateField(verbose_name=_("Start date"))

    # In Finnish: Loppupäivämäärä
    end_date = models.DateField(verbose_name=_("End date"), null=True, blank=True)

    objects = VatManager()

    class Meta:
        verbose_name = pgettext_lazy("Model name", "VAT")
        verbose_name_plural = pgettext_lazy("Model name", "VATs")
        ordering = ("-start_date",)

    def __str__(self):
        return _("VAT {}% {} - {}").format(self.percent, self.start_date, self.end_date)

    def clean(self):
        if (
            Vat.objects.filter(start_date__lte=self.start_date)
            .filter(Q(end_date__gte=self.start_date) | Q(end_date__isnull=True))
            .exclude(id=self.id)
            .count()
            > 0
        ):
            raise ValidationError(_("Only one VAT can be active at a time"))

        if (
            self.end_date
            and Vat.objects.filter(start_date__lte=self.end_date)
            .filter(Q(end_date__gte=self.end_date) | Q(end_date__isnull=True))
            .exclude(id=self.id)
            .count()
            > 0
        ):
            raise ValidationError(_("Only one VAT can be active at a time"))

        if (
            not self.end_date
            and Vat.objects.filter(start_date__gte=self.start_date)
            .exclude(id=self.id)
            .count()
            > 0
        ):
            raise ValidationError(_("Only one VAT can be active at a time"))

    def calculate_amount_without_vat(self, amount_with_vat: Decimal) -> Decimal:
        return Decimal(100 * amount_with_vat / (100 + self.percent)).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )


auditlog.register(Vat)
