from django.db import transaction
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from landuse.models.agreement import LandUseAgreement
from landuse.models.compensation import LandUseCompensation
from landuse.models.contract import Contract
from landuse.models.decision import Decision, DecisionCondition
from landuse.models.invoice import Invoice
from landuse.models.party import (
    AgreementParty,
    BillingDetails,
    ContactPerson,
    InvoiceRecipient,
)
from landuse.models.payment_schedule import PaymentSchedule
from landuse.models.site import AgreementSite
from landuse.permissions import (
    LanduseDjangoModelPermissions,
    check_collection_permissions,
)
from landuse.serializers.agreement import (
    AgreementPartySerializer,
    AgreementPartyWriteSerializer,
    AgreementSiteSerializer,
    AgreementSiteWriteSerializer,
    ContractSerializer,
    DecisionSerializer,
    DecisionWriteSerializer,
    InvoiceSerializer,
    LandUseAgreementListSerializer,
    LandUseAgreementOverviewSerializer,
    LandUseAgreementSerializer,
    LandUseCompensationSerializer,
    LandUseCompensationWriteSerializer,
    PaymentScheduleSerializer,
)
from landuse.views.mixins import LandUseApiEnabledFlagMixin, LandUsePaginationMixin


class LandUseAgreementViewSet(
    LandUseApiEnabledFlagMixin, LandUsePaginationMixin, viewsets.ModelViewSet
):
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
    permission_classes = [LanduseDjangoModelPermissions]

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

    def get_paginated_serializer_response(self, queryset, serializer_class):
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(serializer_class(page, many=True).data)
        return Response(serializer_class(queryset, many=True).data)

    @action(detail=True, methods=("get",))
    def overview(self, request, pk=None):
        agreement = self.get_object()
        return Response(LandUseAgreementOverviewSerializer(agreement).data)

    @action(detail=True, methods=("get", "put"))
    def parties(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = AgreementPartyWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            return self._replace_parties(agreement, serializer.validated_data)

        return self.get_paginated_serializer_response(
            agreement.parties.all(), AgreementPartySerializer
        )

    @transaction.atomic
    def _replace_parties(self, agreement, parties_data):
        existing_parties = {
            party.pk: party for party in agreement.parties.select_for_update()
        }
        check_collection_permissions(
            self.request.user, AgreementParty, existing_parties, parties_data
        )
        retained_ids = {record.get("id") for record in parties_data}
        for party_id, party in existing_parties.items():
            if party_id not in retained_ids:
                for model in (ContactPerson, BillingDetails, InvoiceRecipient):
                    check_collection_permissions(
                        self.request.user,
                        model,
                        model.objects.filter(agreement_party=party).values_list(
                            "pk", flat=True
                        ),
                        [],
                    )
        retained_party_ids = set()
        saved_parties = []

        for party_data in parties_data:
            party_id = party_data.pop("id", None)
            contact_persons = party_data.pop("contact_persons", [])
            billing_details = party_data.pop("billing_details", None)
            invoice_recipient = party_data.pop("invoice_recipient", None)
            existing_party = existing_parties.get(party_id)
            check_collection_permissions(
                self.request.user,
                ContactPerson,
                (
                    existing_party.contact_persons.values_list("pk", flat=True)
                    if existing_party
                    else ()
                ),
                contact_persons,
            )
            for model, record in (
                (BillingDetails, billing_details),
                (InvoiceRecipient, invoice_recipient),
            ):
                existing_id = (
                    model.objects.filter(agreement_party=existing_party)
                    .values_list("pk", flat=True)
                    .first()
                    if existing_party
                    else None
                )
                check_collection_permissions(
                    self.request.user,
                    model,
                    {existing_id} if existing_id else set(),
                    (
                        [{**record, **({"id": existing_id} if existing_id else {})}]
                        if record is not None
                        else []
                    ),
                )

            if party_id is None:
                party = AgreementParty.objects.create(agreement=agreement, **party_data)
            else:
                party = existing_parties.get(party_id)
                if party is None:
                    raise ValidationError(
                        {"id": f"Party {party_id} does not belong to this agreement."}
                    )
                for field, value in party_data.items():
                    setattr(party, field, value)
                party.save()

            retained_party_ids.add(party.pk)
            ContactPerson.objects.filter(agreement_party=party).delete()
            ContactPerson.objects.bulk_create(
                [
                    ContactPerson(agreement_party=party, **contact)
                    for contact in contact_persons
                ]
            )

            if billing_details is None:
                BillingDetails.objects.filter(agreement_party=party).delete()
            else:
                billing_details.pop("id", None)
                BillingDetails.objects.update_or_create(
                    agreement_party=party, defaults=billing_details
                )

            if invoice_recipient is None:
                InvoiceRecipient.objects.filter(agreement_party=party).delete()
            else:
                invoice_recipient.pop("id", None)
                InvoiceRecipient.objects.update_or_create(
                    agreement_party=party, defaults=invoice_recipient
                )

            saved_parties.append(party)

        agreement.parties.exclude(pk__in=retained_party_ids).delete()
        saved_parties = AgreementParty.objects.filter(
            pk__in=[party.pk for party in saved_parties]
        ).prefetch_related("contact_persons", "billing_details")
        return Response(AgreementPartySerializer(saved_parties, many=True).data)

    @action(detail=True, methods=("get", "put"))
    def compensation(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = LandUseCompensationWriteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            existing_id = (
                LandUseCompensation.objects.filter(agreement=agreement)
                .values_list("pk", flat=True)
                .first()
            )
            check_collection_permissions(
                request.user,
                LandUseCompensation,
                {existing_id} if existing_id else set(),
                [{"id": existing_id}] if existing_id else [{}],
            )
            compensation, _ = LandUseCompensation.objects.update_or_create(
                agreement=agreement, defaults=serializer.validated_data
            )
            return Response(LandUseCompensationSerializer(compensation).data)

        try:
            compensation = agreement.compensation
        except LandUseCompensation.DoesNotExist:
            return Response(None)
        return Response(LandUseCompensationSerializer(compensation).data)

    @action(detail=True, methods=("get", "put"))
    def sites(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = AgreementSiteWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            return self._replace_sites(agreement, serializer.validated_data)

        return Response(
            {
                "agreement_sites": AgreementSiteSerializer(
                    agreement.compensation_sites.all(), many=True
                ).data,
            }
        )

    @transaction.atomic
    def _replace_sites(self, agreement, sites_data):
        existing_sites = {
            site.pk: site
            for site in agreement.compensation_sites.select_for_update(of=("self",))
        }
        check_collection_permissions(
            self.request.user, AgreementSite, existing_sites, sites_data
        )
        retained_site_ids = set()
        saved_sites = []

        for site_data in sites_data:
            site_id = site_data.pop("id", None)
            tenure_types = site_data.pop("tenure_types", [])

            if site_id is None:
                site = AgreementSite.objects.create(agreement=agreement, **site_data)
            else:
                site = existing_sites.get(site_id)
                if site is None:
                    raise ValidationError(
                        {"id": f"Site {site_id} does not belong to this agreement."}
                    )
                for field, value in site_data.items():
                    setattr(site, field, value)
                site.save()

            site.tenure_types.set(tenure_types)
            retained_site_ids.add(site.pk)
            saved_sites.append(site.pk)

        agreement.compensation_sites.exclude(pk__in=retained_site_ids).delete()
        sites = (
            AgreementSite.objects.filter(pk__in=saved_sites)
            .select_related("intended_use")
            .prefetch_related("tenure_types")
        )
        return Response(AgreementSiteSerializer(sites, many=True).data)

    @action(detail=True, methods=("get", "put"))
    def decisions(self, request, pk=None):
        agreement = self.get_object()

        if request.method == "PUT":
            serializer = DecisionWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            return self._replace_decisions(agreement, serializer.validated_data)

        return self.get_paginated_serializer_response(
            agreement.decisions.all(), DecisionSerializer
        )

    @transaction.atomic
    def _replace_decisions(self, agreement, decisions_data):
        existing_decisions = {
            decision.pk: decision
            for decision in agreement.decisions.select_for_update()
        }
        check_collection_permissions(
            self.request.user, Decision, existing_decisions, decisions_data
        )
        retained_ids = {record.get("id") for record in decisions_data}
        for decision_id, decision in existing_decisions.items():
            if decision_id not in retained_ids:
                check_collection_permissions(
                    self.request.user,
                    DecisionCondition,
                    decision.conditions.values_list("pk", flat=True),
                    [],
                )
        retained_decision_ids = set()
        saved_decision_ids = []

        for decision_data in decisions_data:
            decision_id = decision_data.pop("id", None)
            conditions = decision_data.pop("conditions", [])
            existing_decision = existing_decisions.get(decision_id)
            check_collection_permissions(
                self.request.user,
                DecisionCondition,
                (
                    existing_decision.conditions.values_list("pk", flat=True)
                    if existing_decision
                    else ()
                ),
                conditions,
            )

            if decision_id is None:
                decision = Decision.objects.create(agreement=agreement, **decision_data)
            else:
                decision = existing_decisions.get(decision_id)
                if decision is None:
                    raise ValidationError(
                        {
                            "id": f"Decision {decision_id} does not belong to this agreement."
                        }
                    )
                for field, value in decision_data.items():
                    setattr(decision, field, value)
                decision.save()

            DecisionCondition.objects.filter(decision=decision).delete()
            DecisionCondition.objects.bulk_create(
                [
                    DecisionCondition(decision=decision, **condition)
                    for condition in conditions
                ]
            )
            retained_decision_ids.add(decision.pk)
            saved_decision_ids.append(decision.pk)

        agreement.decisions.exclude(pk__in=retained_decision_ids).delete()
        decisions = Decision.objects.filter(pk__in=saved_decision_ids).prefetch_related(
            "conditions"
        )
        return Response(DecisionSerializer(decisions, many=True).data)

    @action(detail=True, methods=("get",))
    def contracts(self, request, pk=None):
        agreement = self.get_object()
        return self.get_paginated_serializer_response(
            agreement.contracts.all(), ContractSerializer
        )

    @action(detail=True, methods=("get",), url_path="payment-schedules")
    def payment_schedules(self, request, pk=None):
        agreement = self.get_object()
        return self.get_paginated_serializer_response(
            agreement.payment_schedules.all(), PaymentScheduleSerializer
        )

    @action(detail=True, methods=("get",))
    def invoices(self, request, pk=None):
        agreement = self.get_object()
        return self.get_paginated_serializer_response(
            agreement.invoices.all(), InvoiceSerializer
        )
