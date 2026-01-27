import datetime
import os
import tempfile

import pytest
from django.conf import settings

from laske_export.management.commands import get_payments_from_laske


@pytest.mark.django_db
def test_unimported_files(monkeypatch):
    test_files = [
        "MR_OUT_ID256_8000_20190923_014512.TXT",
        "MR_OUT_ID256_8000_20191002_014527.TXT",
        "MR_OUT_ID256_8000_20191011_014517.TXT",
    ]
    laske_command = get_payments_from_laske.Command()
    with tempfile.TemporaryDirectory() as directory:
        temp_payments_path = f"{directory}/payments"
        monkeypatch.setattr(
            settings, "LASKE_PAYMENTS_IMPORT_LOCATION", temp_payments_path
        )
        os.mkdir(temp_payments_path)
        for test_file in test_files:
            with open(f"{temp_payments_path}/{test_file}", "w") as f:
                f.write("")
        files = laske_command.find_unimported_files()
        assert len(files) == 2
        assert not any(
            "MR_OUT_ID256_8000_20191011_014517.TXT" in file for file in files
        )


@pytest.mark.django_db
@pytest.mark.ftp
def test_download_and_archive_payments_ftp(monkeypatch, setup_ftp, use_ftp):
    ftp = use_ftp
    test_files = [
        "MR_OUT_ID256_8000_20190923_014512.TXT",
        "MR_OUT_ID256_8000_20191002_014527.TXT",
        "MR_OUT_ID256_8000_20191011_014517.TXT",
        "ML_OUT_ID256_8000_20191126_085824.TXT",
    ]
    with tempfile.TemporaryDirectory() as directory:
        for test_file in test_files:
            with open(f"{directory}/{test_file}", "wb+") as f:
                ftp.storbinary(f"STOR {test_file}", f)
    laske_command = get_payments_from_laske.Command()
    with tempfile.TemporaryDirectory() as directory:
        temp_payments_path = f"{directory}/payments"
        monkeypatch.setattr(
            settings, "LASKE_PAYMENTS_IMPORT_LOCATION", temp_payments_path
        )
        os.mkdir(temp_payments_path)
        laske_command.download_payments_ftp()
        archived_files = ftp.nlst("arch/")
        assert "arch/MR_OUT_ID256_8000_20190923_014512.TXT" in archived_files
        assert "arch/ML_OUT_ID256_8000_20191126_085824.TXT" not in archived_files


@pytest.mark.django_db
@pytest.mark.ftp
def test_handle(monkeypatch, setup_ftp, use_ftp):
    ftp = use_ftp
    test_files = [
        "MR_OUT_ID256_8000_20190923_014512.TXT",
        "MR_OUT_ID256_8000_20191002_014527.TXT",
        "MR_OUT_ID256_8000_20191011_014517.TXT",
        "ML_OUT_ID256_8000_20191126_085824.TXT",
    ]
    with tempfile.TemporaryDirectory() as directory:
        for test_file in test_files:
            with open(f"{directory}/{test_file}", "wb+") as f:
                ftp.storbinary(f"STOR {test_file}", f)
    laske_command = get_payments_from_laske.Command()
    with tempfile.TemporaryDirectory() as directory:
        temp_payments_path = f"{directory}/payments"
        monkeypatch.setattr(
            settings, "LASKE_PAYMENTS_IMPORT_LOCATION", temp_payments_path
        )
        os.mkdir(temp_payments_path)
        laske_command.handle()
        ignored_files = ftp.nlst()
        assert ["ML_OUT_ID256_8000_20191126_085824.TXT", "arch"] == ignored_files
        archived_files = ftp.nlst("arch/")
        assert [
            "arch/MR_OUT_ID256_8000_20190923_014512.TXT",
            "arch/MR_OUT_ID256_8000_20191002_014527.TXT",
            "arch/MR_OUT_ID256_8000_20191011_014517.TXT",
        ] == archived_files


@pytest.mark.django_db
def test_parse_date():
    laske_command = get_payments_from_laske.Command()
    parse_date = laske_command.parse_date
    assert parse_date("190923") == datetime.date(year=2019, month=9, day=23)
    assert parse_date("001301") is None, "Should not accept month 13"
    assert parse_date("") is None
    assert parse_date("000000") is None, "Should not accept empty dates"
    assert parse_date("12121211") is None, "Should not accept too long date"
    assert parse_date("abcabc") is None, "Should not accept characters"


@pytest.mark.django_db
def test_get_payment_date():
    laske_command = get_payments_from_laske.Command()
    get_payment_date = laske_command.get_payment_date
    invoice_number = "74028375984265982364"

    value_date = "190923"
    date_of_entry = "230301"
    assert get_payment_date(value_date, date_of_entry, invoice_number) == datetime.date(
        year=2019, month=9, day=23
    ), "Should pick value_date"

    value_date = "190923"
    date_of_entry = "000000"
    assert get_payment_date(value_date, date_of_entry, invoice_number) == datetime.date(
        year=2019, month=9, day=23
    ), "Should pick value_date"

    value_date = "000000"
    date_of_entry = "230301"
    assert get_payment_date(value_date, date_of_entry, invoice_number) == datetime.date(
        year=2023, month=3, day=1
    ), "Should pick date_of_entry"

    value_date = "000000"
    date_of_entry = "000000"
    assert (
        get_payment_date(value_date, date_of_entry, invoice_number) is None
    ), "Should pick nothing"


def test_import_sftp(monkeypatch, mock_sftp):
    """Test mocked SFTP import, does not raise errors."""

    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setattr(settings, "LASKE_PAYMENTS_IMPORT_LOCATION", directory)
        monkeypatch.setattr(
            settings,
            "LASKE_SERVERS",
            {
                "payments": {
                    "host": "localhost",
                    "port": 22,
                    "username": "testuser",
                    "password": "testpass",
                    "directory": "/",
                    "key_type": "rsa",
                    "key": b"-----BEGIN RSA PRIVATE KEY-----\nABCDF\n-----END RSA PRIVATE",
                }
            },
        )
        laske_command = get_payments_from_laske.Command()
        laske_command.download_payments_sftp()
