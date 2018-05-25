import requests
from django.conf import settings
from django.http import Http404, HttpResponseServerError, StreamingHttpResponse, HttpResponse
from requests.auth import HTTPBasicAuth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


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

    r = requests.get(url, data=params, auth=HTTPBasicAuth(settings.KTJ_PRINT_USERNAME, settings.KTJ_PRINT_PASSWORD),
                     stream=True)

    if r.status_code != 200:
        return HttpResponse(status=r.status_code, content=r.content)

    return StreamingHttpResponse(status=r.status_code, reason=r.reason, content_type=r.headers['Content-Type'],
                                 streaming_content=r.raw)
