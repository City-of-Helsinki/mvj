import json
import re

import pytest
from django_extensions.management.commands import show_urls

PK_REPLACEMENT = "12"
ID_REPLACEMENT = "34"
UUID_REPLACEMENT = "001acc16-c45b-4dab-97ee-f79c0292d37b"
TRADEREGISTER_SERVICE_REPLACEMENT = "trade_register/company_extended"

REPLACEMENTS = (
    (re.compile("<pk>"), PK_REPLACEMENT),
    (re.compile(r"<\w+_id>"), ID_REPLACEMENT),  # Replaces `<something_id>` with `34`
    (re.compile("<str:uuid>"), UUID_REPLACEMENT),
    (re.compile("trade_register/<service>"), TRADEREGISTER_SERVICE_REPLACEMENT),
)

# These URLs do not require authentication intentionally
WHITELIST_PUBLIC_URLS = (
    "/v1/pub/answer/",
    "/v1/pub/faq/",
    "/v1/pub/plot_search_ui/0",
    "/v1/pub/plot_search_ui/1",
    "/v1/pub/plot_search_ui/",
)
WHITELIST_DJANGO_URLS = (
    "/admin/",
    "/auth/",
    "/docs/",
    "/redoc/",
    "/__debug__/",
)

WHITELIST = WHITELIST_PUBLIC_URLS + WHITELIST_DJANGO_URLS


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

    def _is_valid_route(route):
        url = route.get("url", "")
        return (
            len(url) > 0
            and not url.startswith(WHITELIST)
            and url.endswith("/")
            and "<format>" not in url
        )

    try:
        views = filter(_is_valid_route, json.loads(views_str))
    except json.JSONDecodeError:
        return []

    paths = []
    for view in views:
        path = view.get("url", "")
        for pattern, replacement in REPLACEMENTS:
            path = re.sub(pattern, replacement, path)
        paths.append(path)
    return paths


@pytest.mark.django_db
@pytest.mark.parametrize("path", get_url_paths())
def test_urls(client, path):
    for method in ["get", "post", "put", "patch", "delete", "options"]:
        request_method = getattr(client, method)
        response = request_method(path)
        assert (
            response.status_code == 401
        ), f"Found unauthenticated endpoint: {method.upper()} {path}"
