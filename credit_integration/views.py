import datetime

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from credit_integration.mapper import map_credit_decision_status
from credit_integration.models import CreditDecision
from credit_integration.permissions import (
    CreditDecisionViewPermission,
    SendCreditDecisionInquiryPermission,
)
from credit_integration.requests import (
    request_company_decision,
    request_consumer_decision,
)
from credit_integration.serializers import (
    CreditDecisionConsumerSerializer,
    CreditDecisionSerializer,
)
from leasing.models import Contact


@api_view(["POST"])
@permission_classes((SendCreditDecisionInquiryPermission,))
def send_credit_decision_inquiry(request):
    """
    Send credit decision inquiry to credit decision service
    """
    customer_id = request.data.get("customer_id")
    business_id = request.data.get("business_id")
    identity_number = request.data.get("identity_number")

    if request.method == "POST" and (customer_id or business_id or identity_number):
        contact = None
        if customer_id:
            contact = Contact.objects.get(pk=customer_id)
            if contact.business_id:
                business_id = contact.business_id
            if contact.national_identification_number:
                identity_number = contact.national_identification_number

        json_data = None
        if business_id:
            json_data = request_company_decision(business_id, request.user.username)
            CreditDecision.create_credit_decision_by_json(
                json_data, request.user, contact
            )
        if identity_number:
            json_data = request_consumer_decision(
                identity_number, request.user.username
            )

        credit_decision_serializer = CreditDecisionSerializer()
        if customer_id or business_id:
            credit_decision_queryset = CreditDecision.get_credit_decision_queryset_by_customer(
                customer_id=customer_id, business_id=business_id
            )

            credit_decision_serializer = CreditDecisionSerializer(
                credit_decision_queryset, many=True
            )

            return Response(credit_decision_serializer.data)

        if identity_number:
            serializer_data = [
                {
                    "status": map_credit_decision_status(
                        json_data["consumerResponse"]["decisionProposalData"][
                            "decisionProposal"
                        ]["proposal"]["code"]
                    ),
                    "official_name": json_data["consumerResponse"][
                        "decisionProposalData"
                    ]["customerData"]["name"],
                    "claimant": request.user,
                    "created_at": datetime.datetime.now(),
                    "reasons": [],
                }
            ]

            for factor in json_data["consumerResponse"]["decisionProposalData"][
                "decisionProposal"
            ]["proposal"]["factorRow"]:
                serializer_data[0]["reasons"].append(
                    {"reason_code": factor["code"], "reason": factor["text"]}
                )

            serializer = CreditDecisionConsumerSerializer(serializer_data, many=True)
            return Response(serializer.data)

    return Response(None, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes((CreditDecisionViewPermission,))
def get_credit_decisions(request):
    """
    Get credit decisions by customer id or business id
    """
    customer_id = request.query_params.get("customer_id")
    business_id = request.query_params.get("business_id")

    if request.method == "GET" and (customer_id or business_id):
        if customer_id or business_id:
            credit_decision_queryset = CreditDecision.get_credit_decision_queryset_by_customer(
                customer_id=customer_id, business_id=business_id
            )

            credit_decision_serializer = CreditDecisionSerializer(
                credit_decision_queryset, many=True
            )

            return Response(credit_decision_serializer.data)

    return Response(None, status=status.HTTP_400_BAD_REQUEST)
