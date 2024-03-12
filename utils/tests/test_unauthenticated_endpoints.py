# -*- coding: utf-8 -*-
import json

import pytest
import requests
from django_extensions.management.commands import show_urls


def get_url_paths():
    cmd = show_urls.Command()
    views_str = cmd.handle(
        no_color=True,
        language=None,
        decorator=None,
        format_style="pretty-json",
        urlconf="ROOT_URLCONF",
        unsorted=True,
    )
    views = json.loads(views_str)
    whitelist = """
        /auth/login/
        /auth/logout/
        /v1/pub/answer/
        /v1/pub/faq/
        /v1/pub/plot_search_ui/0
        /v1/pub/plot_search_ui/1
        /v1/pub/plot_search_ui/
        /docs/
        /redoc/
    """.split()
    repls = (
        ("/<pk>\\.<format>/", "/1234.json/"),
        ("/<pk>/", "/1234/"),
        ("/<path:object_id>/", "/abc/123/"),
    )
    paths = []
    for view in views:
        path = view.get("url")
        if path:
            if (
                not path.endswith("/")
                or path.startswith("/admin/")
                or path in whitelist
            ):
                continue
            for r in repls:
                path = path.replace(*r)
            if ">" in path:
                continue  # This includes lone '\.<format>' and few corner cases
            paths.append(path)
    return paths


@pytest.mark.parametrize("path", get_url_paths())
def test_urls(path):
    url = f"http://localhost:8001{path}"
    response = requests.get(url, headers={"Accept": "application/json"})
    assert (
        response.status_code == 401
    ), f"Found unauthenticated endpoint # curl -L -v {url}"
