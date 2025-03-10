from io import BytesIO

import sentry_sdk
from django.conf import settings
from django.http import FileResponse, QueryDict
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from xhtml2pdf import pisa

from credit_integration.exceptions import AsiakastietoAPIError
from credit_integration.mapper import map_consumer_response
from credit_integration.models import CreditDecision, CreditDecisionLog
from credit_integration.permissions import (
    CreditDecisionViewPermission,
    SendCreditDecisionInquiryPermission,
    SendSanctionsInquiryPermission,
)
from credit_integration.requests import (
    request_company_decision,
    request_company_sanctions,
    request_consumer_decision,
    request_consumer_sanctions,
)
from credit_integration.serializers import (
    CreditDecisionConsumerSerializer,
    CreditDecisionSerializer,
)
from credit_integration.types import (
    CompanySanctionsResponse,
    PepAndSanctionsData,
    WatchListSearchResponse,
)
from leasing.models import Contact
from users.models import User

TRANSLATION_MAP = {
    # Commented out keys are marked here to exist, but we don't want to translate those,
    # as some of them are being accessed in templates directly.
    # "hitCount": "Osumien määrä",
    # "watchListHits": "Osumat listalla",
    # "hitsRow": "Osumarivi",
    "watchListType": "Listan tyyppi",
    "hitId": "Osuman tunniste",
    "names": "Nimet",
    "name": "Nimi",
    "role": "Rooli",
    "prefix": "Etuliite",
    "firstName": "Etunimi",
    "lastName": "Sukunimi",
    "suffix": "Loppuliite",
    "aka": "Tunnetaan myös nimellä",
    "primaryName": "Pääasiallinen nimi",
    "identifiers": "Tunnisteet",
    "entityId": "Entiteetin tunniste",
    "directId": "Suora tunniste",
    "passportId": "Passin tunniste",
    "nationalId": "Henkilön tunniste",
    "otherId": "Muu tunniste",
    "parentId": "Emo tunniste",
    "entityType": "Entiteetin tyyppi",
    "description": "Kuvaus",
    "dateOfBirth": "Syntymäaika 1",
    "dateOfBirth2": "Syntymäaika 2",
    "placeOfBirth": "Syntymäpaikka",
    "country": "Maa",
    "touchDate": "Muokattu",
    "addresses": "Osoitteet",
    "addressRow": "Osoiterivit",
    "addressId": "Osoitteen tunniste",
    "addressDetails": "Osoitteen tiedot",
    "city": "Kaupunki",
    "stateProvince": "Osavaltio/Maakunta",
    "postalCode": "Postinumero",
    "remarks": "Huomiot",
    "addressSource": "Osoitelähde",
    "addressSourceAbbreviation": "Osoitelähteen lyhenne",
    "addressSourceName": "Osoitelähteen nimi",
    "addressSourceCountry": "Osoitelähteen maa",
    "entitySource": "Entiteetin lähde",
    "entitySourceAbbreviation": "Entiteettilähteen lyhenne",
    "entitySourceName": "Entiteettilähteen nimi",
    "entitySourceCountry": "Entiteettilähteen maa",
    "effectiveDate": "Voimaantulopäivä",
    "expirationDate": "Vanhenemispäivä",
}


@api_view(["POST"])
@permission_classes((SendCreditDecisionInquiryPermission,))
def send_credit_decision_inquiry(request: Request):
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
            credit_decision_queryset = (
                CreditDecision.get_credit_decision_queryset_by_customer(
                    customer_id=customer_id, business_id=business_id
                )
            )
            credit_decision_serializer = CreditDecisionSerializer(
                credit_decision_queryset, many=True
            )
            return Response(credit_decision_serializer.data)

    return Response(None, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes((CreditDecisionViewPermission,))
def get_credit_decisions(request: Request):
    """
    Get credit decisions by customer id or business id
    """
    customer_id = request.query_params.get("customer_id")
    business_id = request.query_params.get("business_id")

    if business_id:
        business_id = business_id.replace("-", "")

    if request.method == "GET" and (customer_id or business_id):
        if customer_id or business_id:
            credit_decision_queryset = (
                CreditDecision.get_credit_decision_queryset_by_customer(
                    customer_id=customer_id, business_id=business_id
                )
            )

            credit_decision_serializer = CreditDecisionSerializer(
                credit_decision_queryset, many=True
            )

            return Response(credit_decision_serializer.data)

    return Response(None, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes((SendSanctionsInquiryPermission,))
def send_sanctions_inquiry(request: Request):
    """
    Get sanctions inquiry from sanctions service for a company or a person.
    """
    if settings.FLAG_SANCTIONS_INQUIRY is not True:
        return Response(None, status=status.HTTP_403_FORBIDDEN)

    query_params: QueryDict = request.query_params
    business_id = query_params.get("business_id")
    first_name = query_params.get("first_name")
    last_name = query_params.get("last_name")
    birth_year = query_params.get("birth_year")

    if request.method != "GET":
        return Response(None, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    validation_error_response = validate_sanctions_request_params(
        business_id, last_name, birth_year
    )
    if validation_error_response:
        return validation_error_response

    if business_id:
        return handle_company_sanctions(request.user, business_id)

    if last_name:
        return handle_consumer_sanctions(
            request.user, first_name, last_name, birth_year
        )

    return Response(
        {
            "message": "Unknown error.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _error_response(json_error):
    return Response(
        {
            "message": f"{json_error['errorCode']}: {json_error['errorText']}",
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def validate_finnish_business_id(business_id: str) -> bool:
    if len(business_id) != 9:
        return False

    id_part = business_id[:7]
    if not id_part.isdigit():
        return False

    if business_id[7] != "-":
        return False

    checkmark = business_id[8]
    if not checkmark.isdigit():
        return False

    return True


def validate_sanctions_request_params(
    business_id: str, last_name: str, birth_year: str
) -> Response | None:
    if all([business_id, last_name]):
        return Response(
            {
                "message": "Only one of `business_id` or `last_name` allowed.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not any([business_id, last_name]):
        return Response(
            {
                "message": "Missing one of `business_id`, `last_name` in request.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if business_id:
        invalid_response = Response(
            {
                "message": "Invalid `business_id`.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        if not validate_finnish_business_id(business_id):
            return invalid_response

    if birth_year:
        invalid_response = Response(
            {
                "message": "Invalid `birth_year`.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        if len(birth_year) != 4:
            return invalid_response

        if not birth_year.isdigit():
            return invalid_response

    return None


def handle_company_sanctions(user, business_id):
    try:
        pdf_data = _get_company_sanctions_pdf(user, business_id)
    except AsiakastietoAPIError as e:
        sentry_sdk.capture_exception(e)
        return Response(
            {
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return Response(
            {
                "message": "Unknown error while getting company sanctions.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return FileResponse(
        pdf_data,
        as_attachment=True,
        filename=f"pakotelistaus-yritys_{timezone.now().strftime('%Y-%m-%d')}.pdf",
        content_type="application/pdf",
    )


def handle_consumer_sanctions(user, first_name, last_name, birth_year):
    try:
        pdf_data = _get_consumer_sanctions_pdf(user, first_name, last_name, birth_year)
    except AsiakastietoAPIError as e:
        sentry_sdk.capture_exception(e)
        return Response(
            {
                "message": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return Response(
            {
                "message": "Unknown error while getting consumer sanctions.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return FileResponse(
        pdf_data,
        as_attachment=True,
        filename=f"pakotelistaus-henkilo_{timezone.now().strftime('%Y-%m-%d')}.pdf",
        content_type="application/pdf",
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
            business_id,
            user,
            log_text,
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
            identity_number,
            user,
            log_text,
        )

    return json_data, json_error


def _add_log(identification, user, text):
    CreditDecisionLog.objects.create(
        identification=identification, user=user, text=text
    )


def _generate_pdf(context, template_name) -> BytesIO:
    html_source = render_to_string(template_name, context=context)
    output = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_source,
        dest=output,
    )

    if pisa_status.err:
        return Response(
            {
                "message": "PDF generation failed.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    output.seek(0)
    return output


def _get_company_sanctions_pdf(user: User, business_id: str) -> BytesIO:
    business_id_without_dash = business_id.replace("-", "")
    sanctions_response: CompanySanctionsResponse = request_company_sanctions(
        user.username, business_id_without_dash
    )

    sanctions_data: PepAndSanctionsData = sanctions_response.get(
        "companyResponse", {}
    ).get("pepAndSanctionsData", {})
    hitcounts = [
        int(x.get("hitCount", 0)) for x in sanctions_data.get("watchListHits", {})
    ]
    timestamp = timezone.now()
    # Translate dictionary keys to Finnish
    translated_sanctions_data = _translate_keys(
        _sort_dict(sanctions_data), TRANSLATION_MAP
    )
    context = {
        "query": {
            "business_id": business_id,
            "timestamp": timestamp,
            "user_name": (
                user.get_display_name()
                if hasattr(user, "get_display_name")
                else user.username
            ),
        },
        "company": translated_sanctions_data,
        "has_sanction_hits": len(hitcounts) > 0,
        "total_hit_count": sum(hitcounts),
    }
    sanctions_template = "company_sanctions.html"
    pdf_bytes_io = _generate_pdf(context, sanctions_template)
    return pdf_bytes_io


def _get_consumer_sanctions_pdf(
    user: User, first_name: str, last_name: str, birth_year: str
) -> BytesIO:
    sanctions_response: WatchListSearchResponse = request_consumer_sanctions(
        user.username,
        first_name=first_name,
        last_name=last_name,
        birth_year=birth_year,
    )

    sanctions_data = (
        sanctions_response.get("watchListResponse", {})
        .get("watchLists", {})
        .get("category")
    )
    hitcounts = [int(x.get("hitCount", 0)) for x in sanctions_data]
    timestamp = timezone.now()

    # Translate dictionary keys to Finnish
    translated_sanctions_data = _translate_keys(
        _sort_dict(sanctions_data), TRANSLATION_MAP
    )
    context = {
        "query": {
            "first_name": first_name,
            "last_name": last_name,
            "timestamp": timestamp,
            "user_name": (
                user.get_display_name()
                if hasattr(user, "get_display_name")
                else user.username
            ),
        },
        "watchlist": translated_sanctions_data,
        "has_sanction_hits": len(hitcounts) > 0,
        "total_hit_count": sum(hitcounts),
    }
    sanctions_template = "consumer_sanctions.html"
    pdf_bytes_io = _generate_pdf(context, sanctions_template)
    return pdf_bytes_io


def _translate_keys(data, translation_map: dict):
    if isinstance(data, dict):
        return {
            translation_map.get(key, key): _translate_keys(value, translation_map)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [_translate_keys(item, translation_map) for item in data]
    else:
        return data


def _sort_dict(data):
    if isinstance(data, dict):
        sorted_dict = {}
        # First, add keys with string or None values
        # To show values first
        for key, value in sorted(data.items()):
            if isinstance(value, str) or value is None:
                sorted_dict[key] = value
        # Then, add keys with nested structures
        # To show nested structures after
        for key, value in sorted(data.items()):
            if not isinstance(value, str) and value is not None:
                sorted_dict[key] = _sort_dict(value)
        return sorted_dict
    elif isinstance(data, list):
        return [_sort_dict(item) for item in data]
    else:
        return data
