from base64 import decodebytes
from typing import Any, cast

import paramiko
from django.conf import settings


class SFTPManagerError(Exception):
    pass


def _laske_servers() -> dict[str, dict[str, Any]]:
    # LASKE_SERVERS is a project-specific setting, not declared on django-stubs' Settings.
    return cast(dict[str, dict[str, Any]], getattr(settings, "LASKE_SERVERS"))


class SFTPManager:
    _payments = "payments"
    _export = "export"
    _landuse_export = "landuse_export"
    _landuse_payments = "landuse_payments"

    def __init__(self, profile: str | None = None) -> None:
        # Profile check
        if profile is None or profile not in [
            self._payments,
            self._export,
            self._landuse_export,
            self._landuse_payments,
        ]:
            raise SFTPManagerError(
                "SFTP profile must be specified: 'payments', 'export', 'landuse_export' or 'landuse_payments'"
            )

        # Check that all relevant settings are available, will raise SFTPManagerError if not
        self._check_settings(profile)

        # Setup and check local and remote directories
        self._setup_directories(profile)

        # Add destination server host key
        try:
            servers = _laske_servers()
            key: paramiko.PKey
            if servers[profile]["key_type"] == "ssh-ed25519":
                key = paramiko.ed25519key.Ed25519Key(
                    data=decodebytes(servers[profile]["key"])
                )
            elif "ecdsa" in servers[profile]["key_type"]:
                key = paramiko.ecdsakey.ECDSAKey(
                    data=decodebytes(servers[profile]["key"])
                )
            else:
                key = paramiko.rsakey.RSAKey(data=decodebytes(servers[profile]["key"]))

            ssh = paramiko.SSHClient()
            hostkeys = ssh.get_host_keys()
            hostkeys.add(
                servers[profile]["host"],
                servers[profile]["key_type"],
                key,
            )

        except Exception as e:
            raise SFTPManagerError(f"Error setting up client: {str(e)}")

        self._profile = profile
        self.ssh = ssh
        self.sftp: paramiko.SFTPClient | None = None

    def __enter__(self) -> paramiko.SFTPClient:
        servers = _laske_servers()
        try:
            self.ssh.connect(
                hostname=servers[self._profile]["host"],
                port=servers[self._profile]["port"],
                username=servers[self._profile]["username"],
                password=servers[self._profile]["password"],
            )
            self.sftp = self.ssh.open_sftp()

        except Exception as e:
            raise SFTPManagerError(
                f"Error connecting to remote '{self._profile}': {str(e)}"
            )

        return self.sftp

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.sftp:
            self.sftp.close()
        self.ssh.close()

    def _check_settings(self, profile: str | None = None) -> None:
        if profile is None:
            raise SFTPManagerError("No SFTP profile specified")
        servers = _laske_servers() if hasattr(settings, "LASKE_SERVERS") else {}
        if (
            not hasattr(settings, "LASKE_SERVERS")
            or profile not in servers
            or (
                profile == self._payments
                and not hasattr(settings, "LASKE_PAYMENTS_IMPORT_LOCATION")
            )
            or (profile == self._export and not hasattr(settings, "LASKE_EXPORT_ROOT"))
            or (
                profile == self._landuse_payments
                and not hasattr(settings, "SAP_PAYMENTS_LANDUSE_ROOT")
            )
            or not servers.get(profile)
            or not servers[profile].get("host")
            or not servers[profile].get("port")
            or not servers[profile].get("username")
            or not servers[profile].get("password")
            or not servers[profile].get("key_type")
            or not servers[profile].get("key")
            or not servers[profile].get("directory")
        ):
            raise SFTPManagerError("At least one setting is missing, please check.")

    def _setup_directories(self, profile: str | None = None) -> None:
        if profile is None:
            raise SFTPManagerError("No SFTP profile specified")
        servers = _laske_servers()
        try:
            match profile:
                case self._payments:
                    self._localpath = getattr(
                        settings, "LASKE_PAYMENTS_IMPORT_LOCATION"
                    )
                    self._remotepath = servers[self._payments]["directory"]

                case self._export:
                    self._localpath = getattr(settings, "LASKE_EXPORT_ROOT")
                    self._remotepath = servers[self._export]["directory"]
                case self._landuse_export:
                    self._localpath = None
                    self._remotepath = servers[self._landuse_export]["directory"]
                case self._landuse_payments:
                    self._localpath = getattr(settings, "SAP_PAYMENTS_LANDUSE_ROOT")
                    self._remotepath = servers[self._landuse_payments]["directory"]
                case _:
                    raise SFTPManagerError("Invalid SFTP profile specified")
        except SFTPManagerError as se:
            raise se
        except AttributeError as e:
            raise SFTPManagerError(f"Error setting up directories: {str(e)}")
