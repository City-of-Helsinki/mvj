import pytest
from django.test.utils import override_settings
from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch


def reload_urlconf(urlconf=None):
    """Reloads the given urlconf or the ROOT_URLCONF if None is given."""
    import sys
    from importlib import import_module, reload

    from django.conf import settings
    from django.urls import clear_url_caches

    clear_url_caches()
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        reload(sys.modules[urlconf])
    else:
        import_module(urlconf)


@pytest.fixture(scope="function")
def set_plotsearch_flag_reload_urlconf():
    """Set the FLAG_PLOTSEARCH to True before the test and False after the test.
    Reloads urlconf after setting the flag.
    Allows running tests as if the feature was enabled.
    TODO: Remove this fixture when the feature flag is removed."""
    # Before a test function
    with override_settings(FLAG_PLOTSEARCH=True):
        reload_urlconf()
    yield
    # Tear down after a test function
    with override_settings(FLAG_PLOTSEARCH=False):
        reload_urlconf()


def get_urls():
    url_names = [
        {"url_name": "pub_attachment-list", "kwargs": {}},
        {"url_name": "pub_favourite-list", "kwargs": {}},
        {"url_name": "pub_form-list", "kwargs": {}},
        {"url_name": "pub_plot_search-list", "kwargs": {}},
        {"url_name": "pub_plot_search_stage-list", "kwargs": {}},
        {"url_name": "pub_plot_search_type-list", "kwargs": {}},
        {"url_name": "pub_plot_search_subtype-list", "kwargs": {}},
        {
            "url_name": "pub_direct_reservation_to_favourite",
            "kwargs": {"uuid": "123e4567-e89b-12d3-a456-426614174000"},
        },
    ]
    return url_names


def get_test_ids():
    return [url_info["url_name"] for url_info in get_urls()]


@pytest.mark.django_db
@pytest.mark.parametrize("url_info", get_urls(), ids=get_test_ids())
def test_flag_plotsearch_pub_urls_enabled(set_plotsearch_flag_reload_urlconf, url_info):
    url_name = url_info["url_name"]
    kwargs = url_info["kwargs"]
    url = reverse(f"v1:{url_name}", kwargs=kwargs)
    resolver = resolve(url)
    assert resolver.url_name == url_name


@pytest.mark.django_db
@pytest.mark.parametrize("url_info", get_urls(), ids=get_test_ids())
def test_flag_plotsearch_pub_urls_disabled(url_info):
    url_name = url_info["url_name"]
    kwargs = url_info["kwargs"]
    with pytest.raises(NoReverseMatch):
        reverse(f"v1:{url_name}", kwargs=kwargs)


@pytest.mark.django_db
def test_pub_download_should_not_exist(set_plotsearch_flag_reload_urlconf):
    from mvj.urls import pub_router

    views = [x[1] for x in pub_router.registry]
    for view in views:
        has_download = hasattr(view, "download")
        if has_download:
            assert False, f"download should not exist in {view}"
