import os
import tempfile
from pathlib import Path

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
        monkeypatch.setattr(settings, "LASKE_EXPORT_ROOT", directory)
        directory_path = Path(directory)
        os.mkdir(directory_path / "payments")
        for test_file in test_files:
            with open(directory_path / "payments" / test_file, "w") as f:
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
        monkeypatch.setattr(settings, "LASKE_EXPORT_ROOT", directory)
        os.mkdir(f"{directory}/payments")
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
        monkeypatch.setattr(settings, "LASKE_EXPORT_ROOT", directory)
        directory_path = Path(directory)
        os.mkdir(directory_path / "payments")
        laske_command.handle()
        ignored_files = ftp.nlst()
        assert ["ML_OUT_ID256_8000_20191126_085824.TXT", "arch"] == ignored_files
        archived_files = ftp.nlst("arch/")
        assert [
            "arch/MR_OUT_ID256_8000_20190923_014512.TXT",
            "arch/MR_OUT_ID256_8000_20191002_014527.TXT",
            "arch/MR_OUT_ID256_8000_20191011_014517.TXT",
        ] == archived_files
