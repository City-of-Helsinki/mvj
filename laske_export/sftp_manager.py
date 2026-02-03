from base64 import decodebytes

import paramiko
from django.conf import settings


class SFTPManagerError(Exception):
    pass


class SFTPManager:
    _payments = "payments"
    _export = "export"

    def __init__(self, profile: str = None):
        # Profile check
        if profile is None or profile not in [self._payments, self._export]:
            raise SFTPManagerError(
                "SFTP profile must be specified: 'payments' or 'export'"
            )

        # Check that all relevant settings are available, will raise SFTPManagerError if not
        self._check_settings(profile)

        # Setup and check local and remote directories
        self._setup_directories(profile)

        # Add destination server host key
        try:
            if settings.LASKE_SERVERS[profile]["key_type"] == "ssh-ed25519":
                key = paramiko.ed25519key.Ed25519Key(
                    data=decodebytes(settings.LASKE_SERVERS[profile]["key"])
                )
            elif "ecdsa" in settings.LASKE_SERVERS[profile]["key_type"]:
                key = paramiko.ecdsakey.ECDSAKey(
                    data=decodebytes(settings.LASKE_SERVERS[profile]["key"])
                )
            else:
                key = paramiko.rsakey.RSAKey(
                    data=decodebytes(settings.LASKE_SERVERS[profile]["key"])
                )

            ssh = paramiko.SSHClient()
            hostkeys = ssh.get_host_keys()
            hostkeys.add(
                settings.LASKE_SERVERS[profile]["host"],
                settings.LASKE_SERVERS[profile]["key_type"],
                key,
            )

        except Exception as e:
            raise SFTPManagerError(f"Error setting up client: {str(e)}")

        self._profile = profile
        self.ssh = ssh
        self.sftp = None

    def __enter__(self):
        try:
            self.ssh.connect(
                hostname=settings.LASKE_SERVERS[self._profile]["host"],
                port=settings.LASKE_SERVERS[self._profile]["port"],
                username=settings.LASKE_SERVERS[self._profile]["username"],
                password=settings.LASKE_SERVERS[self._profile]["password"],
            )
            self.sftp = self.ssh.open_sftp()

        except Exception as e:
            raise SFTPManagerError(
                f"Error connecting to remote '{self._profile}': {str(e)}"
            )

        return self.sftp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sftp:
            self.sftp.close()
        self.ssh.close()

    def _check_settings(self, profile: str = None):
        if profile is None:
            raise SFTPManagerError("No SFTP profile specified")
        if (
            not hasattr(settings, "LASKE_SERVERS")
            or profile not in settings.LASKE_SERVERS
            or (
                profile == self._payments
                and not hasattr(settings, "LASKE_PAYMENTS_IMPORT_LOCATION")
            )
            or (profile == self._export and not hasattr(settings, "LASKE_EXPORT_ROOT"))
            or not settings.LASKE_SERVERS.get(profile)
            or not settings.LASKE_SERVERS[profile].get("host")
            or not settings.LASKE_SERVERS[profile].get("port")
            or not settings.LASKE_SERVERS[profile].get("username")
            or not settings.LASKE_SERVERS[profile].get("password")
            or not settings.LASKE_SERVERS[profile].get("key_type")
            or not settings.LASKE_SERVERS[profile].get("key")
            or not settings.LASKE_SERVERS[profile].get("directory")
        ):
            raise SFTPManagerError("At least one setting is missing, please check.")

    def _setup_directories(self, profile: str = None):
        if profile is None:
            raise SFTPManagerError("No SFTP profile specified")
        try:
            match profile:

                case self._payments:
                    self._localpath = getattr(
                        settings, "LASKE_PAYMENTS_IMPORT_LOCATION"
                    )
                    self._remotepath = settings.LASKE_SERVERS[self._payments][
                        "directory"
                    ]

                case self._export:
                    self._localpath = getattr(settings, "LASKE_EXPORT_ROOT")
                    self._remotepath = settings.LASKE_SERVERS[self._export]["directory"]
                case _:
                    raise SFTPManagerError("Invalid SFTP profile specified")
        except SFTPManagerError as se:
            raise se
        except AttributeError as e:
            raise SFTPManagerError(f"Error setting up directories: {str(e)}")


####################################################


def test_import_sftp():

    import os
    import stat

    from django.conf import settings

    from laske_export.sftp_manager import SFTPManager, SFTPManagerError

    try:
        lpath = getattr(settings, "LASKE_PAYMENTS_IMPORT_LOCATION")
        rpath = settings.LASKE_SERVERS["payments"]["directory"]
        trfs = []
        with SFTPManager(profile="payments") as sftp:

            for item in sftp.listdir_attr(rpath):
                if stat.S_ISDIR(item.st_mode):
                    pass
                else:
                    sftp.get(
                        os.path.join(rpath, item.filename),
                        os.path.join(lpath, item.filename),
                    )
                    trfs.append(item.filename)
    except SFTPManagerError as e:
        raise e
    except Exception as e:
        raise SFTPManagerError(f"Error during SFTP import test: {str(e)}")
    finally:
        for f in trfs:
            fp = os.path.join(lpath, f)
            if os.path.exists(fp):
                os.remove(fp)


def test_export_sftp():
    import os

    from django.conf import settings

    from laske_export.sftp_manager import SFTPManager, SFTPManagerError

    try:
        filename = "test_export_file.txt"
        with open(filename, "w") as f:
            f.write("This is a test file for SFTP export.\n")

        remote_filepath = settings.LASKE_SERVERS["export"]["directory"]

        with SFTPManager(profile="export") as sftp:
            remote = os.path.join(remote_filepath, filename)
            sftp.put(localpath=filename, remotepath=remote)
            sftp.remove(remote)

    except SFTPManagerError as e:
        raise e
    except Exception as e:
        raise SFTPManagerError(f"Error during SFTP export test: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
