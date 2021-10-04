from auditlog.registry import auditlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from credit_integration.enums import CreditDecisionStatus
from leasing.enums import ContactType
from leasing.models import Contact
from leasing.models.mixins import TimeStampedModel
from users.models import User


class CreditDecisionReason(TimeStampedModel):
    """
    In Finnish: Luottopäätöksen syyn perusteet
    """

    # In Finnish: Syykoodi
    reason_code = models.CharField(
        verbose_name=_("Reason code"), max_length=3, unique=True,
    )

    # In Finnish: Syy
    reason = models.TextField(verbose_name=_("Reason"),)


class CreditDecision(TimeStampedModel):
    """
    In Finnish: Luottopäätös
    """

    # In Finnish: Asiakas
    customer = models.ForeignKey(
        Contact,
        verbose_name=_("Customer"),
        related_name="credit_decisions",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    # In Finnish: Luottopäätöksen tila
    status = EnumField(CreditDecisionStatus, verbose_name=_("Status"), max_length=30)

    # In Finnish: Luottopäätöksen perusteet
    reasons = models.ManyToManyField(
        CreditDecisionReason, verbose_name=_("Reasons"), blank=True
    )

    # In Finnish: Y-tunnus
    business_id = models.CharField(
        verbose_name=_("Business ID"), blank=True, max_length=9,
    )

    # In Finnish: Virallinen nimi
    official_name = models.CharField(
        verbose_name=_("Official name"), blank=True, max_length=255,
    )

    # In Finnish: Osoite
    address = models.CharField(verbose_name=_("Address"), blank=True, max_length=255,)

    # In Finnish: Puhelinnumero
    phone_number = models.CharField(
        verbose_name=_("Phone number"), blank=True, max_length=50,
    )

    # In Finnish: Yhtiömuoto
    business_entity = models.CharField(
        verbose_name=_("Business entity"), blank=True, max_length=50,
    )

    # In Finnish: Toiminnan käynnistämispäivämäärä
    operation_start_date = models.DateField(
        verbose_name=_("Date of commencement of operations"), blank=True,
    )

    # In Finnish: Toimialakoodi
    industry_code = models.CharField(
        verbose_name=_("Industry code"), blank=True, max_length=10,
    )

    # In Finnish: Luottopäätöksen hakija
    claimant = models.ForeignKey(
        User,
        verbose_name=_("Claimant"),
        related_name="credit_decisions",
        on_delete=models.PROTECT,
    )

    @staticmethod
    def get_credit_decision_queryset_by_customer(customer_id=None, business_id=None):
        credit_decision_queryset = None

        if customer_id or business_id:
            if customer_id:
                credit_decision_queryset = CreditDecision.objects.filter(
                    customer_id=customer_id, customer__type=ContactType.BUSINESS
                )
            else:
                credit_decision_queryset = CreditDecision.objects.filter(
                    business_id=business_id
                )
            credit_decision_queryset = credit_decision_queryset.order_by("-created_at")

        return credit_decision_queryset


auditlog.register(CreditDecision)
