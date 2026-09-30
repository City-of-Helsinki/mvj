import hashlib
import json

from django.conf import settings
from django.http import HttpResponseNotModified
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from landuse.models.agreement import (
    DetailedPlanProcessingStage,
    LandUseAgreementStatus,
)
from landuse.models.contract import (
    CollateralBase,
    CollateralDocumentDetailsBase,
    Contract,
    MortgageDeedCollateral,
)
from landuse.models.decision import Decision, DecisionCondition
from landuse.models.invoice import InvoiceItemType, InvoiceStatus, InvoiceType
from landuse.models.party import AgreementPartyRole, PartyType
from landuse.models.payment_schedule import (
    PaymentScheduleItemType,
    PaymentScheduleStatus,
)
from landuse.models.site import AgreementSite
from landuse.views.mixins import LandUseApiEnabledFlagMixin


class LandUseUiMetadataView(LandUseApiEnabledFlagMixin, APIView):
    """Provides the static choice lists required to render Land Use forms."""

    cache_control = "public, max-age=86400, stale-while-revalidate=604800"
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _choices(enum):
        return [{"value": choice.value, "label": str(choice.label)} for choice in enum]

    def get(self, request):
        payload = {
            "agreement_statuses": self._choices(LandUseAgreementStatus),
            "detailed_plan_processing_stages": self._choices(
                DetailedPlanProcessingStage
            ),
            "party_types": self._choices(PartyType),
            "agreement_party_roles": self._choices(AgreementPartyRole),
            "contract_types": self._choices(Contract.ContractType),
            "collateral_types": self._choices(CollateralBase.CollateralType),
            "collateral_document_categories": self._choices(
                CollateralDocumentDetailsBase.DocumentCategory
            ),
            "mortgage_deed_collateral_targets": self._choices(
                MortgageDeedCollateral.CollateralTarget
            ),
            "decision_makers": self._choices(Decision.DecisionMaker),
            "decision_types": self._choices(Decision.DecisionType),
            "decision_condition_types": self._choices(DecisionCondition.ConditionType),
            "invoice_types": self._choices(InvoiceType),
            "invoice_statuses": self._choices(InvoiceStatus),
            "invoice_item_types": self._choices(InvoiceItemType),
            "payment_schedule_statuses": self._choices(PaymentScheduleStatus),
            "payment_schedule_item_types": self._choices(PaymentScheduleItemType),
            "preservation_designations": self._choices(
                AgreementSite.PreservationDesignation
            ),
            "languages": [
                {"value": value, "label": str(label)}
                for value, label in settings.LANGUAGES
            ],
        }
        serialized_payload = json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        )
        etag = f'"{hashlib.sha256(serialized_payload.encode()).hexdigest()}"'

        if request.headers.get("If-None-Match") == etag:
            response = HttpResponseNotModified()
        else:
            response = Response(payload)

        response["Cache-Control"] = self.cache_control
        response["ETag"] = etag
        return response
