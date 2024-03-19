# -*- coding: utf-8 -*-
import pytest
from django_extensions.management.commands import show_urls
import json
import requests
from lxml import html
import mvj.urls


def get_url_paths():
    cmd = show_urls.Command()
    views_str = cmd.handle(
        no_color=True,
        language=None, decorator=None,
        format_style='pretty-json',
        urlconf="ROOT_URLCONF",unsorted=True)
    views = json.loads(views_str)
    return [path for view in views if (path := view.get('url'))]


@pytest.mark.parametrize('path',get_url_paths())
def test_urls(path):
    repls = (('/<pk>\.<format>/','/1234.json/'),
         ('/<pk>/','/1234/'),
         ('/<path:object_id>/','/abc/123/'))
    loginpagetitle = 'Kirjaudu sisään | Django-sivuston ylläpito'
    whitelist = '''
        /auth/login/
        /auth/logout/
        /v1/pub/answer/
        /v1/pub/faq/
        /v1/pub/form/
        /v1/pub/plot_search_ui/0
        /v1/pub/plot_search/
        /v1/pub/plot_search_stage/
        /v1/pub/plot_search_type/
        /v1/pub/plot_search_subtype/
        /v1/pub/plot_search_ui/1
        /docs/
        /redoc/
    ''' .split()
    if not path.endswith('/') or path in whitelist: pytest.skip()
    for r in repls:
        path = path.replace(*r)
    if '>' in path: pytest.skip() # This includes lone '\.<format>' and few corner cases
    url = f'http://localhost:8001{path}'
    response = requests.get(url, headers = {'Content-Type': 'application/json'})
    content_type = response.headers.get('content-type')
    if response.status_code == 200 :
        assert content_type.startswith('text/html;'), f"Got {content_type} response # curl -L {url}"
        # We are viewing internal pages so trusting the title should be adequate
        titles = html.fromstring(response.content).xpath('//title/text()')
        assert titles[0].encode('latin1').decode('utf-8') == loginpagetitle,\
               f"Got non-login {content_type} response # curl -L {url}"
    else:
        assert response.status_code == 401 or response.status_code == 404,\
               f"Got unexpected retcode {response.status_code} # curl -L -v {url}"
