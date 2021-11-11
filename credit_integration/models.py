from auditlog.registry import auditlog
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from credit_integration.enums import CreditDecisionStatus
from credit_integration.mapper import map_credit_decision_status
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

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Credit decision reason")
        verbose_name_plural = pgettext_lazy("Model name", "Credit decision reasons")


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
        verbose_name=_("Date of commencement of operations"), blank=True, null=True
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

    # In Finnish: Alkuperäinen tieto
    original_data = JSONField(
        verbose_name=_("original_data"),
        encoder=DjangoJSONEncoder,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Credit decision")
        verbose_name_plural = pgettext_lazy("Model name", "Credit decisions")
        permissions = [
            ("send_creditdecision_inquiry", "Can send credit decision inquiry",),
        ]

    @staticmethod
    @transaction.atomic
    def create_credit_decision_by_json(json_data, claimant, customer=None):
        """
        Create credit decision object by the Asiakastieto JSON data.
        """

        customer_data = json_data["companyResponse"]["decisionProposalData"][
            "customerData"
        ]
        official_name = customer_data["name"]
        business_id = customer_data["businessId"]

        if "companyData" in json_data["companyResponse"]:
            company_data = json_data["companyResponse"]["companyData"]
            address = company_data["identificationData"]["address"]["street"]
            address += ", " + company_data["identificationData"]["address"]["zip"]
            address += " " + company_data["identificationData"]["address"]["town"]
            phone_number = None
            if company_data["identificationData"]["contactInformation"]:
                phone_number = company_data["identificationData"]["contactInformation"][
                    "phone"
                ]
            industry_code = company_data["identificationData"]["lineOfBusiness"][
                "lineOfBusinessCode"
            ]
            business_entity = company_data["identificationData"]["companyFormText"]
            operation_start_date = company_data["startDate"]

        proposal_data = json_data["companyResponse"]["decisionProposalData"][
            "decisionProposal"
        ]["proposal"]
        status = map_credit_decision_status(proposal_data["code"])

        credit_decision = CreditDecision.objects.create(
            customer=customer,
            status=status,
            business_id=business_id,
            official_name=official_name,
            address=address,
            phone_number=phone_number,
            business_entity=business_entity,
            operation_start_date=operation_start_date,
            industry_code=industry_code,
            claimant=claimant,
            original_data=json_data,
        )

        for factor in proposal_data["factorRow"]:
            reason, _ = CreditDecisionReason.objects.update_or_create(
                reason_code=factor["code"], defaults={"reason": factor["text"]}
            )
            credit_decision.reasons.add(reason)

        return credit_decision

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


class CreditDecisionLog(TimeStampedModel):
    """
    In Finnish: Luottopäätöksen loki
    """

    # In Finnish: Tunniste (Y-tunnus / Hetu)
    identification = models.CharField(verbose_name=_("Identification"), max_length=20,)

    # In Finnish: Käyttäjä
    user = models.ForeignKey(
        User,
        verbose_name=_("User"),
        related_name="credit_decision_logs",
        on_delete=models.PROTECT,
    )

    # In Finnish: Teksti
    text = models.CharField(verbose_name=_("Text"), max_length=255,)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Credit decision log")
        verbose_name_plural = pgettext_lazy("Model name", "Credit decision logs")
        ordering = ["-created_at"]


auditlog.register(CreditDecision)
