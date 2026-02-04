import pytest
from django.conf import settings

from laske_export import sftp_manager
from laske_export.sftp_manager import SFTPManagerError


def test_sftp_invalid_profile():
    with pytest.raises(SFTPManagerError):
        sftp_manager.SFTPManager(profile="invalid_profile")


def test_sftp_missing_settings(monkeypatch):
    # Provide mock settings for invalid 'export' profile
    # missing 'key' setting
    monkeypatch.setattr(
        settings,
        "LASKE_SERVERS",
        {
            "export": {
                "host": "localhost",
                "port": 22,
                "username": "test",
                "password": "test",
                "directory": "/",
                "key_type": "rsa",
            }
        },
    )
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
                "username": "test",
                "password": "test",
                "directory": "/",
                "key_type": "rsa",
                "key": b"AAAAB3NzaC1yc2EAAAADAQABAAABgQCwd76MQfUDhAm7mkKNjT1LEsIdd4Xcx690jGm"
                + b"p2dDQZz3z3fUZoAOdZDsVlbAOY5JkiERgs54I01Rgfjw3ns66jaZdE7CO0xGLnqM8peVm72m7"
                + b"GBCAx8LR5oMJGETrcqcIEl7z6rAKP0Xml+TdwXVhPVH+kdnxfhL/51l0u+GZ50nL0FkGBbmAq"
                + b"uY99dPzDg3SjgFKI+FkpctsjDjtCkq7JKJDALk+spKq2arZ1QZVonyMa6N/S87d8gECscSnJn"
                + b"ZxuY1JCXj6KyiVq5NuTSR03YcLh2wrTS9VaU5ttu3lSUxBMWX9weSZwCzrD9xejYqTv2YNTms"
                + b"Zb0U1nwyoiHIA8Iq3sA65UxQ/bODcVQBGvmyM3+TFoZr5pkq07i9jEWHNbZynkTHJSjI5T8fE"
                + b"dIvBw3bmnFYDs4ZudxiF5Y5ZIsbtitQef/vh15npOgC5mpy5BPxlrYFr1PGynDbry4NFPJDBA"
                + b"Q2YrPSTLkQl+Y+2hWJhbnCDLwQLm1PbYOCG/os= test@example.com",
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
                "username": "test",
                "password": "test",
                "directory": "/tmp/payments",
                "key_type": "rsa",
                "key": b"AAAAB3NzaC1yc2EAAAADAQABAAABgQCwd76MQfUDhAm7mkKNjT1LEsIdd4Xcx690jGm"
                + b"p2dDQZz3z3fUZoAOdZDsVlbAOY5JkiERgs54I01Rgfjw3ns66jaZdE7CO0xGLnqM8peVm72m7"
                + b"GBCAx8LR5oMJGETrcqcIEl7z6rAKP0Xml+TdwXVhPVH+kdnxfhL/51l0u+GZ50nL0FkGBbmAq"
                + b"uY99dPzDg3SjgFKI+FkpctsjDjtCkq7JKJDALk+spKq2arZ1QZVonyMa6N/S87d8gECscSnJn"
                + b"ZxuY1JCXj6KyiVq5NuTSR03YcLh2wrTS9VaU5ttu3lSUxBMWX9weSZwCzrD9xejYqTv2YNTms"
                + b"Zb0U1nwyoiHIA8Iq3sA65UxQ/bODcVQBGvmyM3+TFoZr5pkq07i9jEWHNbZynkTHJSjI5T8fE"
                + b"dIvBw3bmnFYDs4ZudxiF5Y5ZIsbtitQef/vh15npOgC5mpy5BPxlrYFr1PGynDbry4NFPJDBA"
                + b"Q2YrPSTLkQl+Y+2hWJhbnCDLwQLm1PbYOCG/os= test@example.com",
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
