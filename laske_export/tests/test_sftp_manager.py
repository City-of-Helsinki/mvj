import pytest
from django.conf import settings

from laske_export import sftp_manager
from laske_export.sftp_manager import SFTPManagerError


def test_sftp_invalid_profile():
    with pytest.raises(SFTPManagerError):
        sftp_manager.SFTPManager(profile="invalid_profile")


def test_sftp_missing_settings(monkeypatch):
    with pytest.raises(SFTPManagerError):
        sftp_manager.SFTPManager(profile="export")


def test_sftp_valid_profile_export(monkeypatch, mock_sftp):
    # Provide mock settings for 'export' profile
    monkeypatch.setattr(
        settings,
        "LASKE_SERVERS",
        {
            "export": {
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
    monkeypatch.setattr(
        settings,
        "LASKE_EXPORT_ROOT",
        "/tmp/export",
    )
    sftp_mgr = sftp_manager.SFTPManager(profile="export")
    assert sftp_mgr._profile == "export"
    assert sftp_mgr._localpath == getattr(settings, "LASKE_EXPORT_ROOT")
    assert sftp_mgr.ssh is not None  # SSH client should be initialized
    assert sftp_mgr.sftp is None  # SFTP client should not be connected
    with sftp_mgr as sftp:
        assert sftp is not None  # SFTP client should be connected (mocked)


def test_sftp_valid_profile_payments(monkeypatch, mock_sftp):
    # Provide mock settings for 'payments' profile
    monkeypatch.setattr(
        settings,
        "LASKE_SERVERS",
        {
            "payments": {
                "host": "localhost",
                "port": 22,
                "username": "testuser",
                "password": "testpass",
                "directory": "/tmp/payments",
                "key_type": "rsa",
                "key": b"-----BEGIN RSA PRIVATE KEY-----\nABCDF\n-----END RSA PRIVATE",
            }
        },
    )
    monkeypatch.setattr(
        settings,
        "LASKE_PAYMENTS_IMPORT_LOCATION",
        "/tmp/payments",
    )
    sftp_mgr = sftp_manager.SFTPManager(profile="payments")
    assert sftp_mgr._profile == "payments"
    assert sftp_mgr._localpath == getattr(settings, "LASKE_PAYMENTS_IMPORT_LOCATION")
    assert sftp_mgr.ssh is not None  # SSH client should be initialized
    assert sftp_mgr.sftp is None  # SFTP client should not be connected
    with sftp_mgr as sftp:
        assert sftp is not None  # SFTP client should be connected (mocked)
