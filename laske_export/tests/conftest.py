import os
import tempfile

import pytest
from django.conf import settings

from leasing.tests.conftest import *  # noqa


def pytest_configure():
    laske_export_root = tempfile.mkdtemp(prefix="laske-export-")
    settings.LANGUAGE_CODE = "en"
    settings.LASKE_EXPORT_ROOT = laske_export_root
    settings.LASKE_SERVERS = {
        "export": {"host": "localhost", "username": "test", "password": "test"}
    }


def pytest_runtest_setup(item):
    if item.get_closest_marker("ftp") and os.environ.get(
        "TEST_FTP_ACTIVE", False
    ) not in [1, "1", True, "True"]:
        pytest.skip("test requires TEST_FTP_ACTIVE to be true")


ftp_settings = {
    "payments": {
        "host": os.getenv("FTP_HOST", "ftp"),
        "port": 21,
        "username": "test",
        "password": "test",
        "directory": "/payments",
    }
}


@pytest.fixture
def setup_ftp(monkeypatch, use_ftp):
    monkeypatch.setattr(settings, "LASKE_SERVERS", ftp_settings)
    ftp = use_ftp
    ftp.mkd("/payments")
    ftp.cwd("/payments")
    ftp.mkd("arch/")
    yield
    # Cleanup all the folders / files from ftp after test
    ftp.cwd("/payments")
    arch_files = ftp.nlst("arch/")
    payment_files = ftp.nlst()
    for obj in arch_files:
        ftp.delete(obj)
    for payment_file in payment_files:
        try:
            ftp.delete(payment_file)
        except Exception:
            ftp.rmd(payment_file)
            continue
    ftp.cwd("/")
    ftp.rmd("payments/")
    ftp.quit()


@pytest.fixture
def use_ftp():
    from ftplib import FTP

    ftp = FTP(
        host=ftp_settings["payments"]["host"],
        user=ftp_settings["payments"]["username"],
        passwd=ftp_settings["payments"]["password"],
        timeout=100,
    )
    return ftp


@pytest.fixture(scope="function", autouse=True)
def laske_export_from_email(override_config):
    with override_config(LASKE_EXPORT_FROM_EMAIL="john@example.com"):
        yield


@pytest.fixture(scope="function", autouse=True)
def laske_export_announce_email(override_config):
    with override_config(
        LASKE_EXPORT_ANNOUNCE_EMAIL="john@example.com,jane@example.com"
    ):
        yield
