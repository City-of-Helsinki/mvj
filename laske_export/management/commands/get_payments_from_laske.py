import datetime
import glob
import os
import sys
import tempfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from sentry_sdk import capture_exception

from laske_export.models import LaskePaymentsLog
from leasing.models import Invoice, Vat
from leasing.models.invoice import InvoicePayment


def get_import_dir():
    return os.path.join(settings.LASKE_EXPORT_ROOT, "payments")


class Command(BaseCommand):
    help = "Get payments from Laske"

    def download_payments_sftp(self):
        import paramiko
        import pysftp
        from paramiko import SSHException
        from paramiko.py3compat import decodebytes

        try:
            # Add destination server host key
            if settings.LASKE_SERVERS["payments"]["key_type"] == "ssh-ed25519":
                key = paramiko.ed25519key.Ed25519Key(
                    data=decodebytes(settings.LASKE_SERVERS["payments"]["key"])
                )
            elif "ecdsa" in settings.LASKE_SERVERS["payments"]["key_type"]:
                key = paramiko.ecdsakey.ECDSAKey(
                    data=decodebytes(settings.LASKE_SERVERS["payments"]["key"])
                )
            else:
                key = paramiko.rsakey.RSAKey(
                    data=decodebytes(settings.LASKE_SERVERS["payments"]["key"])
                )

            hostkeys = paramiko.hostkeys.HostKeys()
            hostkeys.add(
                settings.LASKE_SERVERS["payments"]["host"],
                settings.LASKE_SERVERS["payments"]["key_type"],
                key,
            )

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = hostkeys
            # Or Disable key check:
            # cnopts.hostkeys = None

            with pysftp.Connection(
                settings.LASKE_SERVERS["payments"]["host"],
                port=settings.LASKE_SERVERS["payments"]["port"],
                username=settings.LASKE_SERVERS["payments"]["username"],
                password=settings.LASKE_SERVERS["payments"]["password"],
                cnopts=cnopts,
            ) as sftp:
                sftp.get_d(
                    settings.LASKE_SERVERS["payments"]["directory"],
                    get_import_dir(),
                    preserve_mtime=True,
                )
        except SSHException as e:
            self.stdout.write("Error with the Laske payments server: {}".format(str(e)))
            capture_exception(e)

    def download_payments_ftp(self):
        from ftplib import FTP

        try:
            ftp = FTP()
            ftp.connect(
                host=settings.LASKE_SERVERS["payments"]["host"],
                port=settings.LASKE_SERVERS["payments"]["port"],
            )
            ftp.login(
                user=settings.LASKE_SERVERS["payments"]["username"],
                passwd=settings.LASKE_SERVERS["payments"]["password"],
            )
            ftp.cwd(settings.LASKE_SERVERS["payments"]["directory"])
        except Exception as e:
            self.stderr.write("Could connect to the server. Error: {}".format(str(e)))
            capture_exception(e)
            return

        try:
            file_list = ftp.nlst()
        except Exception as e:
            self.stderr.write("Could not get file list. Error: {}".format(str(e)))
            capture_exception(e)
            return

        for file_name in file_list:
            if not file_name.lower().startswith("mr_out_"):
                self.stderr.write(
                    'Skipping the file "{}" because its name does not start with "MR_OUT_"'.format(
                        file_name
                    )
                )
                continue

            self.stdout.write('Downloading file "{}".'.format(file_name))
            try:
                fp = open(os.path.join(get_import_dir(), file_name), "wb")
                ftp.retrbinary("RETR {}".format(file_name), fp.write)
                self.stdout.write(
                    "Download complete. Moving it to arch directory on the FTP server."
                )
                ftp.rename(file_name, "arch/{}".format(file_name))
                self.stdout.write("Done.")
            except Exception as e:
                self.stderr.write(
                    'Could not download file "{}". Error: {}'.format(file_name, str(e))
                )
                capture_exception(e)

        ftp.quit()

    def download_payments(self):
        if (
            "key_type" in settings.LASKE_SERVERS["payments"]
            and "key" in settings.LASKE_SERVERS["payments"]
        ):
            self.download_payments_sftp()
        else:
            self.download_payments_ftp()

    def check_import_directory(self):
        if not os.path.isdir(get_import_dir()):
            self.stdout.write(
                'Directory "{}" does not exist. Please create it.'.format(
                    get_import_dir()
                )
            )
            sys.exit(-1)

        try:
            fp = tempfile.TemporaryFile(dir=get_import_dir())
            fp.close()
        except PermissionError:
            self.stdout.write(
                'Can not create file in directory "{}".'.format(get_import_dir())
            )
            sys.exit(-1)

    def find_unimported_files(self):
        all_files = glob.glob(
            get_import_dir() + "/MR_OUT_{}_*".format(settings.LASKE_VALUES["import_id"])
        )
        already_imported_filenames = LaskePaymentsLog.objects.filter(
            is_finished=True
        ).values_list("filename", flat=True)

        return [
            filename
            for filename in all_files
            if Path(filename).name not in already_imported_filenames
        ]

    def get_payment_lines_from_file(self, filename):
        result = []

        with open(filename, "rt", encoding="latin-1") as fp:
            lines = fp.readlines()

        for line in lines:
            line = line.strip("\n")
            if len(line) != 90:
                continue
            if line[0] not in ["3", "5", "7"]:
                continue

            result.append(line)

        return result

    def handle(self, *args, **options):  # NOQA C901 'Command.handle' is too complex
        self.check_import_directory()

        self.stdout.write(
            "Connecting to the Laske payments server and downloading files..."
        )
        self.download_payments()
        self.stdout.write("Done.")

        self.stdout.write("Finding files...")
        filenames = self.find_unimported_files()
        if not filenames:
            self.stdout.write("No new files found. Exiting.")
            return

        self.stdout.write("{} new file(s) found.".format(len(filenames)))

        self.stdout.write("Reading files...")

        for filename in filenames:
            filepath = Path(filename)

            self.stdout.write("Filename: {}".format(filename))
            (
                laske_payments_log_entry,
                created,
            ) = LaskePaymentsLog.objects.get_or_create(
                filename=filepath.name, defaults={"started_at": timezone.now()}
            )

            try:
                lines = self.get_payment_lines_from_file(filename)
            except UnicodeDecodeError as e:
                self.stderr.write(
                    "Error: failed to read file {}! Error {}".format(filename, str(e))
                )
                capture_exception(e)
                continue

            for line in lines:
                filing_code = line[27:43].strip()
                if filing_code[:3] != "288":
                    self.stderr.write(
                        "  Skipped row: filing code ({}) should start with 288".format(
                            filing_code
                        )
                    )
                    continue

                try:
                    invoice_number = int(line[43:63])
                except ValueError:
                    self.stderr.write(
                        "  Skipped row: no invoice number provided in payment row"
                    )
                    continue

                amount = Decimal("{}.{}".format(line[77:85], line[85:87]))
                try:
                    payment_date = datetime.date(
                        year=2000 + int(line[21:23]),
                        month=int(line[23:25]),
                        day=int(line[25:27]),
                    )
                except ValueError:
                    self.stderr.write(
                        "  Skipped row: malformed date in payment row: {}.".format(
                            invoice_number, line[21:27]
                        )
                    )
                    continue

                self.stdout.write(
                    " Invoice #{} amount: {} date: {} filing code: {}".format(
                        invoice_number, amount, payment_date, filing_code
                    )
                )

                try:
                    invoice = Invoice.objects.get(number=invoice_number)
                except Invoice.DoesNotExist:
                    self.stderr.write(
                        '  Skipped row: invoice number "{}" does not exist.'.format(
                            invoice_number
                        )
                    )
                    continue

                if invoice.lease.is_subject_to_vat:
                    vat = Vat.objects.get_for_date(payment_date)
                    if not vat:
                        self.stdout.write(
                            "  Lease is subject to VAT but no VAT percent found for payment date {}!".format(
                                payment_date
                            )
                        )
                        continue

                    amount_without_vat = Decimal(
                        100 * amount / (100 + vat.percent)
                    ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

                    self.stdout.write(
                        "  Lease is subject to VAT. Amount: {} - VAT {}% = {}".format(
                            amount, vat.percent, amount_without_vat
                        )
                    )

                    amount = amount_without_vat

                # If the invoice is paid in parts, the different payments will have the same filing_code.
                # Avoiding duplicate payments by checking only the filing_code will skip legit payments
                # so we'll only the skip adding the payments which match on date and amount as well.
                # NB! It's still possible that someone pays e.g. a 40€ invoice with two separate 20€ payments
                # ...but that situation is so rare that we'll handle it manually.
                if invoice.payments.filter(
                    paid_amount=amount, paid_date=payment_date
                ).exists():
                    self.stdout.write(
                        "  Skipped row: payment with same paid_date and paid_amount exists!"
                    )
                    continue

                invoice_payment = InvoicePayment.objects.create(
                    invoice=invoice,
                    paid_amount=amount,
                    paid_date=payment_date,
                    filing_code=filing_code,
                )
                laske_payments_log_entry.payments.add(invoice_payment)
                invoice.update_amounts()

            laske_payments_log_entry.ended_at = timezone.now()
            laske_payments_log_entry.is_finished = True
            laske_payments_log_entry.save()

        self.stdout.write("Done.")
