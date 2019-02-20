import requests
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseServerError, JsonResponse, StreamingHttpResponse
from django.utils.translation import ugettext_lazy as _
from requests import Session
from requests.auth import HTTPBasicAuth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from zeep import Client, Settings
from zeep.helpers import serialize_object
from zeep.transports import Transport

from leasing.permissions import PerMethodPermission


@api_view()
@permission_classes([IsAuthenticated])
def ktj_proxy(request, base_type, print_type):
    required_settings = ('KTJ_PRINT_ROOT_URL', 'KTJ_PRINT_USERNAME', 'KTJ_PRINT_PASSWORD')

    for required_setting in required_settings:
        if not hasattr(settings, required_setting) or not getattr(settings, required_setting):
            return HttpResponseServerError("Please set {} setting".format(required_setting))

    allowed_types = [
        'kiinteistorekisteriote_oik_tod/rekisteriyksikko',
        'kiinteistorekisteriote_oik_tod/maaraala',
        'kiinteistorekisteriote/rekisteriyksikko',
        'kiinteistorekisteriote/maaraala',
        'lainhuutotodistus_oik_tod',
        'lainhuutotodistus',
        'rasitustodistus_oik_tod',
        'rasitustodistus',
        'vuokraoikeustodistus_oik_tod',
        'vuokraoikeustodistus',
        'muodostumisketju_eteenpain',
        'muodostumisketju_taaksepain',
        'voimassa_olevat_muodostuneet',
        'muodostajarekisteriyksikot_ajankohtana',
        'muodostajaselvitys',
        'yhteystiedot',
        'ktjote_oik_tod/kayttooikeusyksikko',
        'ktjote/kayttooikeusyksikko',
    ]

    allowed_params = [
        'kiinteistotunnus',
        'maaraalatunnus',
        'kohdetunnus',
        'lang',
        'leikkauspvm',
    ]

    if print_type not in allowed_types:
        raise Http404

    url = '{}/{}/tuloste/{}/pdf'.format(settings.KTJ_PRINT_ROOT_URL, base_type, print_type)
    params = request.GET.copy()

    for param in request.GET:
        if param not in allowed_params:
            del params[param]

    r = requests.get(url, params=params, auth=HTTPBasicAuth(settings.KTJ_PRINT_USERNAME, settings.KTJ_PRINT_PASSWORD),
                     stream=True)

    if r.status_code != 200:
        return HttpResponse(status=r.status_code, content=r.content)

    return StreamingHttpResponse(status=r.status_code, reason=r.reason, content_type=r.headers['Content-Type'],
                                 streaming_content=r.raw)


class CloudiaProxy(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {
        'GET': ['leasing.view_contract'],
    }

    def get_view_name(self):
        return _("Cloudia Proxy")

    def get(self, request, format=None, contract_id=None, file_id=None):
        data = {
            "extid": contract_id,
        }

        if not file_id:
            url = '{}/api/export/contract/files'.format(settings.CLOUDIA_ROOT_URL)
        else:
            if not file_id.isdigit() and not file_id == 'contractdocument':
                raise APIException(_('file_id parameter is not valid'))

            url = '{}/api/export/contract/files/{}'.format(settings.CLOUDIA_ROOT_URL, file_id)

        r = requests.post(url, json=data, auth=HTTPBasicAuth(settings.CLOUDIA_USERNAME, settings.CLOUDIA_PASSWORD),
                          stream=True)

        if r.status_code != 200:
            return HttpResponse(status=r.status_code, content=r.content)

        return StreamingHttpResponse(status=r.status_code, reason=r.reason, content_type=r.headers['Content-Type'],
                                     streaming_content=r.raw)


class VirreProxy(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {
        'GET': ['leasing.view_invoice'],
    }

    def get_view_name(self):
        return _("Virre Proxy")

    def get(self, request, format=None, service=None, business_id=None):
        known_services = {
             'company_extended': 'CompanyExtendedInfo',
             'company_represent': 'CompanyRepresentInfo',
             'company_notice': 'CompanyNoticeInfo',
             'trade_register_entry': 'TradeRegisterEntryInfo',
        }
        known_pdf_services = [
            'trade_register_entry',
        ]

        if service not in known_services.keys():
            raise APIException(_('service parameter is not valid'))

        session = Session()
        session.auth = HTTPBasicAuth(settings.VIRRE_USERNAME, settings.VIRRE_PASSWORD)
        soap_settings = Settings(strict=False)

        wsdl_service = '{}Service'.format(known_services[service])

        client = Client(
            '{host}/IDSServices11/{wsdl_service}?wsdl'.format(host=settings.VIRRE_API_URL,
                                                              wsdl_service=wsdl_service),
            transport=Transport(session=session),
            settings=soap_settings,
        )

        data = {
            "userId": settings.VIRRE_USERNAME,
            "businessId": business_id,
        }
        action = 'get{}'.format(known_services[service])
        result = getattr(client.service, action)(**data)

        if service in known_pdf_services:
            # example: 'TradeRegisterEntryInfo' -> 'tradeRegisterEntryInfoResponseDetails'
            response_key = '{}ResponseDetails'.format(
                known_services[service][0].lower() + known_services[service][1:])

            if response_key not in result:
                raise APIException(_('business id is invalid'))

            raw_pdf = result[response_key]['extract']

            response = HttpResponse(raw_pdf, content_type='application/pdf')
            response['Content-Disposition'] = (
                'attachment; filename={}_{}.pdf'.format(service, business_id)
            )
            return response

        else:
            return JsonResponse(serialize_object(result))
