from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from credit_integration.models import CreditDecision
from credit_integration.serializers import CreditDecisionSerializer
from leasing.permissions import PerMethodPermission


@api_view(["POST"])
@permission_classes((PerMethodPermission,))
def send_credit_decision_inquiry(request):
    """
    Send credit decision inquiry to credit decision service
    """
    customer_id = request.data.get("customer_id")
    business_id = request.data.get("business_id")
    identity_number = request.data.get("identity_number")

    if request.method == "POST" and (customer_id or business_id or identity_number):
        # TODO: Call the Asiakatieto service

        # TODO: Save the result to database if business, otherwise map the data to return data

        credit_decision_serializer = CreditDecisionSerializer()
        if customer_id or business_id:
            credit_decision_queryset = CreditDecision.get_credit_decision_queryset_by_customer(
                customer_id=customer_id, business_id=business_id
            )

            credit_decision_serializer = CreditDecisionSerializer(
                credit_decision_queryset, many=True
            )

            return Response(credit_decision_serializer.data)

    return Response(None, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes((PerMethodPermission,))
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
