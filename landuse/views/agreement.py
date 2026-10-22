from django.db import transaction
from django.db.models import Prefetch
from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from landuse.models.agreement import LandUseAgreement
from landuse.models.compensation import LandUseCompensation
from landuse.models.contract import (
    CashDepositCollateral,
    Contract,
    ContractChange,
    DepositPledgeCollateral,
    MortgageDeedCollateral,
    MortgageDeedPropertyIdentifier,
    OtherCollateral,
    PersonalGuaranteeCollateral,
)
from landuse.models.decision import Decision, DecisionCondition
from landuse.models.invoice import Invoice
from landuse.models.party import (
    AgreementParty,
    BillingDetails,
    ContactPerson,
    InvoiceRecipient,
)
from landuse.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleInstallment,
    PaymentScheduleInstallmentItem,
)
from landuse.models.site import AgreementSite
from landuse.permissions import LanduseDjangoModelPermissions
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


class ReferencedResourceConflict(APIException):
    status_code = 409
    default_code = "referenced_resource"


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
                        "mortgagedeedcollateral_collaterals__parties",
                        "mortgagedeedcollateral_collaterals__property_identifiers",
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
        removed_ids = set(existing_parties) - {
            party.get("id") for party in parties_data
        }
        referenced_ids = set(
            PaymentSchedule.objects.filter(
                recipient_party_id__in=removed_ids
            ).values_list("recipient_party_id", flat=True)
        ) | set(
            Invoice.objects.filter(recipient_party_id__in=removed_ids).values_list(
                "recipient_party_id", flat=True
            )
        )
        if referenced_ids:
            raise ReferencedResourceConflict(
                {
                    "code": "referenced_parties",
                    "ids": sorted(referenced_ids),
                    "detail": "Remove financial references before deleting these parties.",
                }
            )
        retained_party_ids = set()
        saved_parties = []

        for party_data in parties_data:
            party_id = party_data.pop("id", None)
            contact_persons = party_data.pop("contact_persons", [])
            billing_details = party_data.pop("billing_details", None)
            invoice_recipient = party_data.pop("invoice_recipient", None)

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

        try:
            agreement.parties.exclude(pk__in=retained_party_ids).delete()
        except ProtectedError as error:
            raise ReferencedResourceConflict(
                {
                    "code": "referenced_parties",
                    "detail": "Remove financial references before deleting these parties.",
                }
            ) from error
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
            compensation, _ = LandUseCompensation.objects.update_or_create(
                agreement=agreement, defaults=serializer.validated_data
            )
            return Response(LandUseCompensationSerializer(compensation).data)

        try:
            compensation = agreement.compensation
        except LandUseCompensation.DoesNotExist:
            return Response(None)
        return Response(LandUseCompensationSerializer(compensation).data)

    @action(detail=True, methods=("put",), url_path="compensation-with-sites")
    @transaction.atomic
    def compensation_with_sites(self, request, pk=None):
        agreement = self.get_object()
        serializer = CompensationWithSitesWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        compensation_data = serializer.validated_data["compensation"]
        sites_data = serializer.validated_data["sites"]
        compensation, _ = LandUseCompensation.objects.update_or_create(
            agreement=agreement, defaults=compensation_data
        )
        self._replace_sites(agreement, sites_data)
        return Response(
            {
                "compensation": LandUseCompensationSerializer(compensation).data,
                "sites": AgreementSiteSerializer(
                    agreement.compensation_sites.select_related(
                        "intended_use"
                    ).prefetch_related("tenure_types"),
                    many=True,
                ).data,
            }
        )

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
        removed_ids = set(existing_decisions) - {
            decision.get("id") for decision in decisions_data
        }
        referenced_ids = set(
            Contract.objects.filter(decision_id__in=removed_ids).values_list(
                "decision_id", flat=True
            )
        )
        referenced_ids.update(
            ContractChange.objects.filter(decision_id__in=removed_ids).values_list(
                "decision_id", flat=True
            )
        )
        if referenced_ids:
            raise ReferencedResourceConflict(
                {
                    "code": "referenced_decisions",
                    "ids": sorted(referenced_ids),
                    "detail": "Unlink contracts before deleting these decisions.",
                }
            )
        retained_decision_ids = set()
        saved_decision_ids = []

        for decision_data in decisions_data:
            decision_id = decision_data.pop("id", None)
            conditions = decision_data.pop("conditions", [])

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

    @action(detail=True, methods=("get", "put"))
    def contracts(self, request, pk=None):
        agreement = self.get_object()
        if request.method == "PUT":
            serializer = ContractWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            return self._replace_contracts(agreement, serializer.validated_data)
        return self.get_paginated_serializer_response(
            agreement.contracts.all(), ContractSerializer
        )

    @transaction.atomic
    def _replace_contracts(self, agreement, contracts_data):  # noqa: C901
        existing_contracts = {
            contract.pk: contract
            for contract in agreement.contracts.select_for_update()
        }
        retained_contract_ids = set()
        saved_contract_ids = []
        collateral_models = {
            "MORTGAGE_DEED": MortgageDeedCollateral,
            "CASH_DEPOSIT": CashDepositCollateral,
            "PERSONAL_GUARANTEE": PersonalGuaranteeCollateral,
            "DEPOSIT_PLEDGE": DepositPledgeCollateral,
            "OTHER": OtherCollateral,
        }

        for contract_data in contracts_data:
            contract_id = contract_data.pop("id", None)
            changes_data = contract_data.pop("changes", [])
            collaterals_data = contract_data.pop("collaterals", [])
            self._validate_decisions(agreement, [contract_data, *changes_data])
            if contract_id is None:
                contract = Contract.objects.create(agreement=agreement, **contract_data)
            else:
                contract = existing_contracts.get(contract_id)
                if contract is None:
                    raise ValidationError(
                        {
                            "id": f"Contract {contract_id} does not belong to this agreement."
                        }
                    )
                for field, value in contract_data.items():
                    setattr(contract, field, value)
                contract.save()

            existing_changes = {
                change.pk: change for change in contract.changes.select_for_update()
            }
            retained_change_ids = set()
            for change_data in changes_data:
                change_id = change_data.pop("id", None)
                if change_id is None:
                    change = ContractChange.objects.create(
                        contract=contract, **change_data
                    )
                else:
                    change = existing_changes.get(change_id)
                    if change is None:
                        raise ValidationError(
                            {
                                "id": (
                                    f"Contract change {change_id} does not belong "
                                    f"to contract {contract.pk}."
                                )
                            }
                        )
                    for field, value in change_data.items():
                        setattr(change, field, value)
                    change.save()
                retained_change_ids.add(change.pk)
            contract.changes.exclude(pk__in=retained_change_ids).delete()

            existing_collaterals = {}
            for model in collateral_models.values():
                existing_collaterals.update(
                    {
                        collateral.pk: collateral
                        for collateral in model.objects.select_for_update().filter(
                            contract=contract
                        )
                    }
                )
            retained_collateral_ids = set()
            for collateral_data in collaterals_data:
                collateral_id = collateral_data.pop("id", None)
                party_ids = collateral_data.pop("parties", [])
                property_identifiers = collateral_data.pop("property_identifiers", [])
                collateral_model = collateral_models.get(
                    collateral_data["guarantee_type"]
                )
                if collateral_model is None:
                    raise ValidationError(
                        {"guarantee_type": "Unsupported collateral type."}
                    )
                if not set(party_ids).issubset(
                    set(agreement.parties.values_list("pk", flat=True))
                ):
                    raise ValidationError(
                        {"parties": "Collateral parties must belong to this agreement."}
                    )
                collateral_fields = {
                    field.name
                    for field in collateral_model._meta.get_fields()
                    if getattr(field, "concrete", False) and field.name != "id"
                }
                collateral_data = {
                    field: value
                    for field, value in collateral_data.items()
                    if field in collateral_fields
                }
                if collateral_id is None:
                    collateral = collateral_model.objects.create(
                        contract=contract, **collateral_data
                    )
                else:
                    collateral = existing_collaterals.get(collateral_id)
                    if collateral is None or not isinstance(
                        collateral, collateral_model
                    ):
                        raise ValidationError(
                            {
                                "id": (
                                    f"Collateral {collateral_id} does not belong "
                                    f"to contract {contract.pk}."
                                )
                            }
                        )
                    for field, value in collateral_data.items():
                        setattr(collateral, field, value)
                    collateral.save()
                collateral.parties.set(party_ids)
                if isinstance(collateral, MortgageDeedCollateral):
                    collateral.property_identifiers.all().delete()
                    MortgageDeedPropertyIdentifier.objects.bulk_create(
                        [
                            MortgageDeedPropertyIdentifier(
                                collateral=collateral, identifier=identifier
                            )
                            for identifier in property_identifiers
                        ]
                    )
                retained_collateral_ids.add(collateral.pk)
            for model in collateral_models.values():
                model.objects.filter(contract=contract).exclude(
                    pk__in=retained_collateral_ids
                ).delete()
            retained_contract_ids.add(contract.pk)
            saved_contract_ids.append(contract.pk)
        agreement.contracts.exclude(pk__in=retained_contract_ids).delete()
        contracts = Contract.objects.filter(pk__in=saved_contract_ids).prefetch_related(
            "changes",
            "mortgagedeedcollateral_collaterals__parties",
            "mortgagedeedcollateral_collaterals__property_identifiers",
            "cashdepositcollateral_collaterals__parties",
            "personalguaranteecollateral_collaterals__parties",
            "depositpledgecollateral_collaterals__parties",
            "othercollateral_collaterals__parties",
        )
        return Response(ContractSerializer(contracts, many=True).data)

    def _validate_decisions(self, agreement, records):
        decision_ids = {
            record.get("decision").pk for record in records if record.get("decision")
        }
        valid_ids = set(
            agreement.decisions.filter(pk__in=decision_ids).values_list("pk", flat=True)
        )
        if decision_ids != valid_ids:
            raise ValidationError(
                {"decision": "Contract decisions must belong to this agreement."}
            )

    @action(detail=True, methods=("get", "put"), url_path="payment-schedules")
    def payment_schedules(self, request, pk=None):
        agreement = self.get_object()
        if request.method == "PUT":
            serializer = PaymentScheduleWriteSerializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            return self._replace_payment_schedules(agreement, serializer.validated_data)
        return self.get_paginated_serializer_response(
            agreement.payment_schedules.all(), PaymentScheduleSerializer
        )

    @transaction.atomic
    def _replace_payment_schedules(self, agreement, schedules_data):  # noqa: C901
        existing_schedules = {
            schedule.pk: schedule
            for schedule in agreement.payment_schedules.select_for_update()
        }
        retained_schedule_ids = set()
        saved_schedule_ids = []
        party_ids = set(agreement.parties.values_list("pk", flat=True))
        contract_ids = set(agreement.contracts.values_list("pk", flat=True))
        for schedule_data in schedules_data:
            schedule_id = schedule_data.pop("id", None)
            installments_data = schedule_data.pop("installments")
            if (
                schedule_data["recipient_party"].pk not in party_ids
                or schedule_data["contract"].pk not in contract_ids
            ):
                raise ValidationError(
                    {
                        "detail": (
                            "Payment schedule party and contract must belong to "
                            "this agreement."
                        )
                    }
                )
            if schedule_id is None:
                schedule = PaymentSchedule.objects.create(
                    agreement=agreement, **schedule_data
                )
                schedule.full_clean()
                schedule.save()
            else:
                schedule = existing_schedules.get(schedule_id)
                if schedule is None:
                    raise ValidationError(
                        {
                            "id": f"Payment schedule {schedule_id} does not belong to this agreement."
                        }
                    )
                if schedule.status not in ("DRAFT", "REJECTED"):
                    raise ValidationError(
                        {"status": "Only draft or rejected schedules can be edited."}
                    )
                for field, value in schedule_data.items():
                    setattr(schedule, field, value)
                schedule.full_clean()
                schedule.save()
            existing_installments = {
                installment.pk: installment
                for installment in schedule.installments.select_for_update()
            }
            retained_installment_ids = set()
            sequences = set()
            for installment_data in installments_data:
                installment_id = installment_data.pop("id", None)
                items_data = installment_data.pop("items")
                sequence = installment_data["installment_sequence_number"]
                if sequence in sequences:
                    raise ValidationError(
                        {"installments": "Installment sequence numbers must be unique."}
                    )
                sequences.add(sequence)
                if installment_id is None:
                    installment = PaymentScheduleInstallment.objects.create(
                        payment_schedule=schedule, **installment_data
                    )
                else:
                    installment = existing_installments.get(installment_id)
                    if installment is None:
                        raise ValidationError(
                            {
                                "id": (
                                    f"Installment {installment_id} does not belong "
                                    f"to payment schedule {schedule.pk}."
                                )
                            }
                        )
                    for field, value in installment_data.items():
                        setattr(installment, field, value)
                    installment.save()
                existing_items = {
                    item.pk: item for item in installment.items.select_for_update()
                }
                retained_item_ids = set()
                for item_data in items_data:
                    item_id = item_data.pop("id", None)
                    if item_id is None:
                        item = PaymentScheduleInstallmentItem.objects.create(
                            installment=installment, **item_data
                        )
                    else:
                        item = existing_items.get(item_id)
                        if item is None:
                            raise ValidationError(
                                {
                                    "id": (
                                        f"Installment item {item_id} does not belong "
                                        f"to installment {installment.pk}."
                                    )
                                }
                            )
                        for field, value in item_data.items():
                            setattr(item, field, value)
                        item.save()
                    retained_item_ids.add(item.pk)
                installment.items.exclude(pk__in=retained_item_ids).delete()
                retained_installment_ids.add(installment.pk)
            schedule.installments.exclude(pk__in=retained_installment_ids).delete()
            retained_schedule_ids.add(schedule.pk)
            saved_schedule_ids.append(schedule.pk)
        for schedule in agreement.payment_schedules.exclude(
            pk__in=retained_schedule_ids
        ):
            if schedule.status not in ("DRAFT", "REJECTED"):
                raise ValidationError(
                    {"status": "Only draft or rejected schedules can be deleted."}
                )
            schedule.delete()
        schedules = (
            PaymentSchedule.objects.filter(pk__in=saved_schedule_ids)
            .select_related("recipient_party", "contract")
            .prefetch_related("installments__items")
        )
        return Response(PaymentScheduleSerializer(schedules, many=True).data)

    @action(detail=True, methods=("get",))
    def invoices(self, request, pk=None):
        agreement = self.get_object()
        return self.get_paginated_serializer_response(
            agreement.invoices.all(), InvoiceSerializer
        )
