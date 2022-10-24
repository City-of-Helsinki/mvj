from auditlog.middleware import AuditlogMiddleware
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from credit_integration.mapper import map_consumer_response
from credit_integration.models import CreditDecision, CreditDecisionLog
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
    AuditlogMiddleware().process_request(request)

    customer_id = request.data.get("customer_id")
    business_id = request.data.get("business_id")
    identity_number = request.data.get("identity_number")

    if request.method == "POST" and (customer_id or business_id or identity_number):
        contact = None
        if customer_id:
            contact = Contact.objects.get(pk=customer_id)
            if contact.business_id:
                business_id = contact.business_id
            elif contact.national_identification_number:
                identity_number = contact.national_identification_number
            else:
                return Response(
                    {
                        "message": _(
                            "Cannot find business id or national identification number in customer data."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        json_data = None
        json_error = None
        if business_id:
            business_id = business_id.replace("-", "")

            json_data, json_error = _get_company_decision(
                business_id, request.user, contact
            )

        if identity_number:
            json_data, json_error = _get_consumer_decision(
                identity_number, request.user
            )

        if json_error:
            return _error_response(json_error)

        if identity_number:
            serializer_data = map_consumer_response(json_data, request)
            serializer = CreditDecisionConsumerSerializer(serializer_data, many=True)
            return Response(serializer.data)

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
@permission_classes((CreditDecisionViewPermission,))
def get_credit_decisions(request):
    """
    Get credit decisions by customer id or business id
    """
    customer_id = request.query_params.get("customer_id")
    business_id = request.query_params.get("business_id")

    if business_id:
        business_id = business_id.replace("-", "")

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


def _error_response(json_error):
    return Response(
        {
            "message": "{0}: {1}".format(
                json_error["errorCode"], json_error["errorText"],
            )
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _get_company_decision(business_id, user, contact=None):
    json_data = request_company_decision(business_id, user.username)
    json_error = None
    log_text = "The company response received successfully."

    if (
        "errorMessage" in json_data["companyResponse"]
        and json_data["companyResponse"]["errorMessage"] is not None
    ):
        json_error = json_data["companyResponse"]["errorMessage"]
        log_text = "The company response contains error: {0}: {1}".format(
            json_error["errorCode"], json_error["errorText"]
        )
    else:
        CreditDecision.create_credit_decision_by_json(json_data, user, contact)

    if log_text:
        _add_log(
            business_id, user, log_text,
        )

    return json_data, json_error


def _get_consumer_decision(identity_number, user):
    json_data = request_consumer_decision(identity_number, user.username)
    json_error = None
    log_text = "The consumer response received successfully."

    if (
        "errorMessage" in json_data["consumerResponse"]
        and json_data["consumerResponse"]["errorMessage"] is not None
    ):
        json_error = json_data["consumerResponse"]["errorMessage"]
        log_text = "The consumer response contains error: {0}: {1}".format(
            json_error["errorCode"], json_error["errorText"]
        )

    if log_text:
        _add_log(
            identity_number, user, log_text,
        )

    return json_data, json_error


def _add_log(identification, user, text):
    CreditDecisionLog.objects.create(
        identification=identification, user=user, text=text
    )
