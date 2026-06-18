import requests
from django.conf import settings
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseServerError,
    JsonResponse,
    StreamingHttpResponse,
)
from django.utils.translation import gettext_lazy as _
from requests import Session
from requests.auth import HTTPBasicAuth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from zeep import Client, Settings
from zeep.helpers import serialize_object
from zeep.transports import Transport

from integrations.ryyti import (
    DocumentOption,
    MediaType,
    RyytiClient,
    RyytiException,
)
from leasing.permissions import PerMethodPermission


def are_settings_available(required_settings):
    for required_setting in required_settings:
        if not hasattr(settings, required_setting) or not getattr(
            settings, required_setting
        ):
            return False

    return True


@api_view()
@permission_classes([IsAuthenticated])
def ktj_proxy(request, base_type, print_type):
    required_settings = (
        "KTJ_PRINT_ROOT_URL",
        "KTJ_PRINT_USERNAME",
        "KTJ_PRINT_PASSWORD",
    )

    if not are_settings_available(required_settings):
        return HttpResponseServerError(
            "Please set all required settings: {}".format(", ".join(required_settings))
        )

    allowed_types = [
        "kiinteistorekisteriote_oik_tod/rekisteriyksikko",
        "kiinteistorekisteriote_oik_tod/maaraala",
        "kiinteistorekisteriote/rekisteriyksikko",
        "kiinteistorekisteriote/maaraala",
        "lainhuutotodistus_oik_tod",
        "lainhuutotodistus",
        "rasitustodistus_oik_tod",
        "rasitustodistus",
        "vuokraoikeustodistus_oik_tod",
        "vuokraoikeustodistus",
        "muodostumisketju_eteenpain",
        "muodostumisketju_taaksepain",
        "voimassa_olevat_muodostuneet",
        "muodostajarekisteriyksikot_ajankohtana",
        "muodostajaselvitys",
        "yhteystiedot",
        "ktjote_oik_tod/kayttooikeusyksikko",
        "ktjote/kayttooikeusyksikko",
    ]

    allowed_params = [
        "kiinteistotunnus",
        "maaraalatunnus",
        "kohdetunnus",
        "lang",
        "leikkauspvm",
    ]

    if print_type not in allowed_types:
        raise Http404

    url = "{}/{}/tuloste/{}/pdf".format(
        settings.KTJ_PRINT_ROOT_URL, base_type, print_type
    )
    params = request.GET.copy()

    for param in request.GET:
        if param not in allowed_params:
            del params[param]

    r = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(settings.KTJ_PRINT_USERNAME, settings.KTJ_PRINT_PASSWORD),
        stream=True,
    )

    if r.status_code != 200:
        content = _("Error in upstream service")
        if settings.DEBUG:
            content = r.content

        return HttpResponse(status=r.status_code, content=content)

    return StreamingHttpResponse(
        status=r.status_code,
        reason=r.reason,
        content_type=r.headers["Content-Type"],
        streaming_content=r.raw,
    )


class CloudiaProxy(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_contract"]}

    def get_view_name(self):
        return _("Cloudia Proxy")

    def get(self, request, format=None, contract_id=None, file_id=None):
        required_settings = ("CLOUDIA_ROOT_URL", "CLOUDIA_USERNAME", "CLOUDIA_PASSWORD")

        if not are_settings_available(required_settings):
            return HttpResponseServerError(
                "Please set all required settings: {}".format(
                    ", ".join(required_settings)
                )
            )

        data = {"extid": contract_id}

        if not file_id:
            url = "{}/api/export/contract/files".format(settings.CLOUDIA_ROOT_URL)
        else:
            if not file_id.isdigit() and not file_id == "contractdocument":
                raise APIException(_("file_id parameter is not valid"))

            url = "{}/api/export/contract/file/{}".format(
                settings.CLOUDIA_ROOT_URL, file_id
            )

        r = requests.post(
            url,
            json=data,
            auth=HTTPBasicAuth(settings.CLOUDIA_USERNAME, settings.CLOUDIA_PASSWORD),
            stream=True,
        )

        if r.status_code != 200:
            content = _("Error in upstream service")
            if settings.DEBUG:
                content = r.content

            return HttpResponse(status=r.status_code, content=content)

        return StreamingHttpResponse(
            status=r.status_code,
            reason=r.reason,
            content_type=r.headers["Content-Type"],
            streaming_content=r.raw,
        )


class VirreProxy(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_invoice"]}

    def get_view_name(self):
        return _("Virre Proxy")

    def get(self, request, format=None, service=None, business_id=None):
        required_settings = ("VIRRE_API_URL", "VIRRE_USERNAME", "VIRRE_PASSWORD")

        if not are_settings_available(required_settings):
            return HttpResponseServerError(
                "Please set all required settings: {}".format(
                    ", ".join(required_settings)
                )
            )

        known_services = {
            "company_extended": "CompanyExtendedInfo",
            "company_represent": "CompanyRepresentInfo",
            "company_notice": "CompanyNoticeInfo",
            "trade_register_entry": "TradeRegisterEntryInfo",
            "statute": "StatuteInfoV2",
        }
        known_pdf_services = {
            "trade_register_entry": {
                "response_key": "tradeRegisterEntryInfoResponseDetails",
                "pdf_key": "extract",
            },
            "statute": {
                "response_key": "statuteInfoResponseTypeDetails",
                "pdf_key": "statute",
            },
        }

        if service not in known_services.keys():
            raise APIException(_("service parameter is not valid"))

        session = Session()
        session.auth = HTTPBasicAuth(settings.VIRRE_USERNAME, settings.VIRRE_PASSWORD)
        soap_settings = Settings(strict=False)

        wsdl_service = "{}Service".format(known_services[service])

        client = Client(
            "{host}/IDSServices11/{wsdl_service}?wsdl".format(
                host=settings.VIRRE_API_URL, wsdl_service=wsdl_service
            ),
            transport=Transport(session=session),
            settings=soap_settings,
        )

        data = {"userId": settings.VIRRE_USERNAME, "businessId": business_id}
        action = "get{}".format(known_services[service])
        result = getattr(client.service, action)(**data)

        if service in known_pdf_services.keys():
            response_key = known_pdf_services[service]["response_key"]
            pdf_key = known_pdf_services[service]["pdf_key"]

            if response_key not in result:
                raise APIException(_("business id is invalid"))

            try:
                response = HttpResponse(
                    result[response_key][pdf_key], content_type="application/pdf"
                )
            except KeyError:
                raise APIException(_("File not available"))

            response["Content-Disposition"] = "attachment; filename={}_{}.pdf".format(
                service, business_id
            )
            return response

        else:
            return JsonResponse(serialize_object(result))


class RyytiApiProxy(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_invoice"]}
    STREAM_CHUNK_SIZE = 8 * 1024  # 8 * 1024 = 8192 bytes

    def get_view_name(self):
        return _("Ryyti API Proxy")

    def get(self, request, api=None, business_id=None):
        client = RyytiClient()
        available_apis = self._get_api_registry(client, business_id)

        if api not in available_apis:
            raise APIException(_("Unknown API: {api_name}").format(api_name=api))

        api_method = available_apis[api]

        try:
            api_response = api_method()
        except RyytiException as e:
            raise APIException(
                _("Ryyti API error: {error_msg}").format(error_msg=str(e))
            )

        if not api_response or api_response.status_code != 200:
            raise APIException(_("Data not available"))

        content_type: str = api_response.headers.get("Content-Type", "")
        response = StreamingHttpResponse(
            api_response.iter_content(chunk_size=self.STREAM_CHUNK_SIZE),
            content_type=content_type,
        )

        if content_type.startswith(MediaType.PDF):
            response["Content-Disposition"] = (
                f"inline; filename=ryyti_{business_id}.pdf"
            )

        return response

    def _get_api_registry(self, client, business_id):
        return {
            "organisation_rules_pdf": lambda: client.get_pdf_document(
                document_option=DocumentOption.ORGANISATION_RULES,
                business_id=business_id,
                stream=True,
            ),
            "company_info_json": lambda: client.get_company_info(
                business_id, stream=True
            ),
            "get_company_notifications_json": lambda: client.get_notifications(
                business_id=business_id,
                stream=True,
            ),
            "trade_register_json": lambda: client.get_trade_register_extract(
                business_id=business_id, stream=True
            ),
        }
