from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from landuse.models.agreement import LandUseAgreement
from landuse.models.contract import Contract
from landuse.models.decision import Decision
from landuse.models.invoice import Invoice
from landuse.models.party import AgreementParty
from landuse.models.payment_schedule import PaymentSchedule
from landuse.models.site import AgreementSite
from landuse.serializers.agreement import (
    AgreementPartySerializer,
    AgreementSiteSerializer,
    ContractSerializer,
    DecisionSerializer,
    DetailedPlanSiteSerializer,
    InvoiceSerializer,
    LandUseAgreementListSerializer,
    LandUseAgreementOverviewSerializer,
    LandUseAgreementSerializer,
    LandUseCompensationSerializer,
    PaymentScheduleSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin


class PreconditionFailed(APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = "The agreement has changed. Reload it before saving."
    default_code = "precondition_failed"


class LandUseAgreementViewSet(LandUseApiEnabledFlagMixin, viewsets.ModelViewSet):
    serializer_class = LandUseAgreementSerializer
    filterset_fields = (
        "identifier",
        "status",
        "agreement_type",
        "district",
        "detailed_plan",
        "estimated_presentation_year",
        "estimated_payment_year",
    )

    def get_queryset(self):
        queryset = LandUseAgreement.objects.order_by("-modified_at", "pk")

        if self.action == "list":
            return queryset.select_related("district")

        if self.action in ("retrieve", "overview"):
            return queryset.select_related(
                "district", "authorized_signatory", "detailed_plan"
            ).prefetch_related("addresses", "preparers__preparer")

        if self.action == "parties":
            return queryset.prefetch_related(
                Prefetch(
                    "parties",
                    queryset=AgreementParty.objects.prefetch_related(
                        "contact_persons", "billing_details"
                    ),
                )
            )
        if self.action == "sites":
            return queryset.prefetch_related(
                "detailed_plan_sites",
                Prefetch(
                    "compensation_sites",
                    queryset=AgreementSite.objects.select_related(
                        "intended_use"
                    ).prefetch_related("tenure_types"),
                ),
            )
        if self.action == "decisions":
            return queryset.prefetch_related(
                Prefetch(
                    "decisions",
                    queryset=Decision.objects.prefetch_related("conditions"),
                )
            )
        if self.action == "contracts":
            return queryset.prefetch_related(
                Prefetch(
                    "contracts",
                    queryset=Contract.objects.prefetch_related(
                        "changes",
                        "mortgage_deed_collaterals__parties",
                        "mortgage_deed_collaterals__property_identifiers",
                        "cash_deposit_collaterals__parties",
                        "personal_guarantee_collaterals__parties",
                        "deposit_pledge_collaterals__parties",
                        "other_collaterals__parties",
                    ),
                )
            )
        if self.action == "payment_schedules":
            return queryset.prefetch_related(
                Prefetch(
                    "payment_schedules",
                    queryset=PaymentSchedule.objects.select_related(
                        "recipient_party", "contract"
                    ).prefetch_related("installments__items"),
                )
            )
        if self.action == "invoices":
            return queryset.prefetch_related(
                Prefetch(
                    "invoices",
                    queryset=Invoice.objects.select_related(
                        "recipient_party", "recipient_snapshot"
                    ).prefetch_related("items", "payments"),
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return LandUseAgreementListSerializer
        if self.action in ("retrieve", "overview"):
            return LandUseAgreementOverviewSerializer
        return LandUseAgreementSerializer

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        response["ETag"] = self._etag(self.get_object())
        return response

    def update(self, request, *args, **kwargs):
        agreement = self.get_object()
        if request.headers.get("If-Match") != self._etag(agreement):
            raise PreconditionFailed
        response = super().update(request, *args, **kwargs)
        response["ETag"] = self._etag(self.get_object())
        return response

    @staticmethod
    def _etag(agreement):
        return f'"{agreement.modified_at.isoformat()}"'

    @action(detail=True, methods=("get",))
    def overview(self, request, pk=None):
        agreement = self.get_object()
        response = Response(LandUseAgreementOverviewSerializer(agreement).data)
        response["ETag"] = self._etag(agreement)
        return response

    @action(detail=True, methods=("get",))
    def parties(self, request, pk=None):
        agreement = self.get_object()
        return Response(
            AgreementPartySerializer(agreement.parties.all(), many=True).data
        )

    @action(detail=True, methods=("get",))
    def compensation(self, request, pk=None):
        agreement = self.get_object()
        try:
            compensation = agreement.compensation
        except LandUseAgreement.compensation.RelatedObjectDoesNotExist:
            return Response(None)
        return Response(LandUseCompensationSerializer(compensation).data)

    @action(detail=True, methods=("get",))
    def sites(self, request, pk=None):
        agreement = self.get_object()
        return Response(
            {
                "detailed_plan_sites": DetailedPlanSiteSerializer(
                    agreement.detailed_plan_sites.all(), many=True
                ).data,
                "agreement_sites": AgreementSiteSerializer(
                    agreement.compensation_sites.all(), many=True
                ).data,
            }
        )

    @action(detail=True, methods=("get",))
    def decisions(self, request, pk=None):
        agreement = self.get_object()
        return Response(DecisionSerializer(agreement.decisions.all(), many=True).data)

    @action(detail=True, methods=("get",))
    def contracts(self, request, pk=None):
        agreement = self.get_object()
        return Response(ContractSerializer(agreement.contracts.all(), many=True).data)

    @action(detail=True, methods=("get",), url_path="payment-schedules")
    def payment_schedules(self, request, pk=None):
        agreement = self.get_object()
        return Response(
            PaymentScheduleSerializer(agreement.payment_schedules.all(), many=True).data
        )

    @action(detail=True, methods=("get",))
    def invoices(self, request, pk=None):
        agreement = self.get_object()
        return Response(InvoiceSerializer(agreement.invoices.all(), many=True).data)
