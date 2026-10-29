from django.db import transaction
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from landuse.models.agreement import LandUseAgreement
from landuse.models.compensation import LandUseCompensation
from landuse.models.contract import Contract
from landuse.models.decision import Decision
from landuse.models.invoice import Invoice
from landuse.models.party import AgreementParty
from landuse.models.payment_schedule import PaymentSchedule
from landuse.models.site import AgreementSite
from landuse.permissions import LanduseDjangoModelPermissions, tab_permission
from landuse.serializers.agreement import (
    AgreementPartySerializer,
    AgreementPartyWriteSerializer,
    AgreementSiteSerializer,
    AgreementSiteWriteSerializer,
    CompensationWithSitesWriteSerializer,
    ContractSerializer,
    ContractWriteSerializer,
    DecisionSerializer,
    DecisionWriteSerializer,
    InvoiceSerializer,
    LandUseAgreementListSerializer,
    LandUseAgreementOverviewSerializer,
    LandUseAgreementSerializer,
    LandUseCompensationSerializer,
    LandUseCompensationWriteSerializer,
    PaymentScheduleSerializer,
    PaymentScheduleWriteSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin, LandUsePaginationMixin


class LandUseAgreementViewSet(
    LandUseApiEnabledFlagMixin, LandUsePaginationMixin, viewsets.ModelViewSet
):
    serializer_class = LandUseAgreementSerializer
    filterset_fields = (
        "identifier",
        "status",
        "district",
        "detailed_plan",
        "estimated_presentation_year",
        "estimated_payment_year",
    )
    permission_classes = [LanduseDjangoModelPermissions]

    def get_queryset(self):
        queryset = LandUseAgreement.objects.order_by("-modified_at", "pk")

        if self.action == "list":
            return queryset.select_related(
                "district", "detailed_plan"
            ).prefetch_related("parties", "compensation_sites")

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
                        "mortgagedeedcollateral_collaterals__parties",
                        "cashdepositcollateral_collaterals__parties",
                        "personalguaranteecollateral_collaterals__parties",
                        "depositpledgecollateral_collaterals__parties",
                        "othercollateral_collaterals__parties",
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

    def get_paginated_serializer_response(self, queryset, serializer_class):
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(serializer_class(page, many=True).data)
        return Response(serializer_class(queryset, many=True).data)

    @action(detail=True, methods=("get",))
    def overview(self, request, pk=None):
        agreement = self.get_object()
        return Response(LandUseAgreementOverviewSerializer(agreement).data)

    @action(
        detail=True,
        methods=("get", "put"),
        permission_classes=[tab_permission("parties")],
    )
    def parties(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = AgreementPartyWriteSerializer(
                agreement.parties.all(), data=request.data, many=True
            )
            serializer.is_valid(raise_exception=True)
            parties = serializer.save(agreement=agreement)
            return Response(AgreementPartySerializer(parties, many=True).data)

        return self.get_paginated_serializer_response(
            agreement.parties.all(), AgreementPartySerializer
        )

    @action(
        detail=True,
        methods=("get", "put"),
        permission_classes=[tab_permission("compensation")],
    )
    def compensation(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = LandUseCompensationWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            compensation, _ = LandUseCompensation.objects.update_or_create(
                agreement=agreement, defaults=serializer.validated_data
            )
            return Response(LandUseCompensationSerializer(compensation).data)

        try:
            compensation = agreement.compensation
        except LandUseCompensation.DoesNotExist:
            return Response(None)
        return Response(LandUseCompensationSerializer(compensation).data)

    @action(
        detail=True,
        methods=("put",),
        url_path="compensation-with-sites",
        permission_classes=[tab_permission("compensation"), tab_permission("sites")],
    )
    @transaction.atomic
    def compensation_with_sites(self, request, pk=None):
        agreement = self.get_object()
        serializer = CompensationWithSitesWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        compensation, _ = LandUseCompensation.objects.update_or_create(
            agreement=agreement, defaults=serializer.validated_data["compensation"]
        )
        sites_serializer = AgreementSiteWriteSerializer(
            agreement.compensation_sites.all(), data=request.data["sites"], many=True
        )
        sites_serializer.is_valid(raise_exception=True)
        sites = sites_serializer.save(agreement=agreement)
        return Response(
            {
                "compensation": LandUseCompensationSerializer(compensation).data,
                "sites": AgreementSiteSerializer(sites, many=True).data,
            }
        )

    @action(
        detail=True,
        methods=("get", "put"),
        permission_classes=[tab_permission("sites")],
    )
    def sites(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = AgreementSiteWriteSerializer(
                agreement.compensation_sites.all(), data=request.data, many=True
            )
            serializer.is_valid(raise_exception=True)
            sites = serializer.save(agreement=agreement)
            return Response(AgreementSiteSerializer(sites, many=True).data)

        return Response(
            {
                "agreement_sites": AgreementSiteSerializer(
                    agreement.compensation_sites.all(), many=True
                ).data,
            }
        )

    @action(
        detail=True,
        methods=("get", "put"),
        permission_classes=[tab_permission("decisions")],
    )
    def decisions(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = DecisionWriteSerializer(
                agreement.decisions.all(), data=request.data, many=True
            )
            serializer.is_valid(raise_exception=True)
            decisions = serializer.save(agreement=agreement)
            return Response(DecisionSerializer(decisions, many=True).data)

        return self.get_paginated_serializer_response(
            agreement.decisions.all(), DecisionSerializer
        )

    @action(
        detail=True,
        methods=("get", "put"),
        permission_classes=[tab_permission("contracts")],
    )
    def contracts(self, request, pk=None):
        agreement = self.get_object()
        if request.method == "PUT":
            serializer = ContractWriteSerializer(
                agreement.contracts.all(), data=request.data, many=True
            )
            serializer.is_valid(raise_exception=True)
            contracts = serializer.save(agreement=agreement)
            return Response(ContractSerializer(contracts, many=True).data)
        return self.get_paginated_serializer_response(
            agreement.contracts.all(), ContractSerializer
        )

    @action(
        detail=True,
        methods=("get", "put"),
        url_path="payment-schedules",
        permission_classes=[tab_permission("payment_schedules")],
    )
    def payment_schedules(self, request, pk=None):
        agreement = self.get_object()
        if request.method == "PUT":
            serializer = PaymentScheduleWriteSerializer(
                agreement.payment_schedules.all(), data=request.data, many=True
            )
            serializer.is_valid(raise_exception=True)
            schedules = serializer.save(agreement=agreement)
            return Response(PaymentScheduleSerializer(schedules, many=True).data)
        return self.get_paginated_serializer_response(
            agreement.payment_schedules.all(), PaymentScheduleSerializer
        )

    @action(
        detail=True, methods=("get",), permission_classes=[tab_permission("invoices")]
    )
    def invoices(self, request, pk=None):
        agreement = self.get_object()
        return self.get_paginated_serializer_response(
            agreement.invoices.all(), InvoiceSerializer
        )
