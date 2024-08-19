import datetime
import glob
import os
import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from sentry_sdk import capture_exception

from laske_export.models import LaskePaymentsLog
from leasing.models import Invoice, Lease, ServiceUnit, Vat
from leasing.models.invoice import InvoicePayment


def get_import_dir():
    return os.path.join(settings.LASKE_EXPORT_ROOT, "payments")


class Command(BaseCommand):
    help = "Get payments from Laske"

    def download_payments_sftp(self):
        from base64 import decodebytes

        import paramiko
        import pysftp
        from paramiko import SSHException

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
            self.stdout.write(f"Error with the Laske payments server: {str(e)}")
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
            self.stderr.write(f"Could connect to the server. Error: {str(e)}")
            capture_exception(e)
            return

        try:
            file_list = ftp.nlst()
        except Exception as e:
            self.stderr.write(f"Could not get file list. Error: {str(e)}")
            capture_exception(e)
            return

        for file_name in file_list:
            if not file_name.lower().startswith("mr_out_"):
                self.stderr.write(
                    f'Skipping the file "{file_name}" because its name does not start with "MR_OUT_"'
                )
                continue

            self.stdout.write(f'Downloading file "{file_name}".')
            try:
                fp = open(os.path.join(get_import_dir(), file_name), "wb")
                ftp.retrbinary(f"RETR {file_name}", fp.write)
                self.stdout.write(
                    "Download complete. Moving it to arch directory on the FTP server."
                )
                ftp.rename(file_name, f"arch/{file_name}")
                self.stdout.write("Done.")
            except Exception as e:
                self.stderr.write(
                    f'Could not download file "{file_name}". Error: {str(e)}'
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
                f'Directory "{get_import_dir()}" does not exist. Please create it.'
            )
            sys.exit(-1)

        try:
            fp = tempfile.TemporaryFile(dir=get_import_dir())
            fp.close()
        except PermissionError:
            self.stdout.write(f'Can not create file in directory "{get_import_dir}".')
            sys.exit(-1)

    def _get_service_unit_import_ids(self):
        return {su.laske_import_id for su in ServiceUnit.objects.all()}

    def find_unimported_files(self):
        all_files = []
        import_id_regexp = f"MR_OUT_({'|'.join(self._get_service_unit_import_ids())})_"
        for filename in glob.glob(f"{get_import_dir()}/MR_OUT_*"):
            if re.search(import_id_regexp, filename):
                all_files.append(filename)

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

    def parse_date(self, date_str: str) -> Optional[datetime.date]:
        """
        Parameters:
        date_str: A date in the format 'YYMMDD'
        """
        if len(date_str) != 6:
            # Format expects 6 characters long strings
            return None
        try:
            return datetime.date(
                # Laske uses 2-digit years
                year=2000 + int(date_str[0:2]),
                month=int(date_str[2:4]),
                day=int(date_str[4:6]),
            )
        except ValueError:
            return None

    def get_payment_date(
        self, value_date_str: str, date_of_entry_str: str, invoice_number: str
    ) -> Optional[datetime.date]:
        """
        Use either `value date` or `date of entry` as the payment date.
        `value date` is set to be "000000" when the payment is acknowledged some other way.
        """
        # Arvopäivä
        value_date = self.parse_date(value_date_str)
        # Kirjauspäivä
        date_of_entry = self.parse_date(date_of_entry_str)
        payment_date = value_date or date_of_entry
        if value_date is None and date_of_entry is not None:
            self.stdout.write(
                f"  Using date_of_entry as payment_date, malformed value_date in payment row: "
                f"{invoice_number} {value_date_str}."
            )
        return payment_date

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

        self.stdout.write(f"{len(filenames)} new file(s) found.")

        self.stdout.write("Reading files...")

        for filename in filenames:
            filepath = Path(filename)

            self.stdout.write(f"Filename: {filename}")
            (
                laske_payments_log_entry,
                created,
            ) = LaskePaymentsLog.objects.get_or_create(
                filename=filepath.name, defaults={"started_at": timezone.now()}
            )

            try:
                lines: List[str] = self.get_payment_lines_from_file(filename)
            except UnicodeDecodeError as e:
                self.stderr.write(
                    f"Error: failed to read file {filename}! Error {str(e)}"
                )
                capture_exception(e)
                continue

            for line in lines:
                filing_code = line[27:43].strip()
                # Filing code series 288 = KYMP, 297 = KuVa
                if filing_code[:3] not in ["288", "297"]:
                    self.stderr.write(
                        f"  Skipped row: filing code ({filing_code}) should start with 288 or 297"
                    )
                    continue

                try:
                    invoice_number = int(line[43:63])
                except ValueError:
                    self.stderr.write(
                        "  Skipped row: no invoice number provided in payment row"
                    )
                    continue

                whole_number_part = line[77:85]
                fractional_part = line[85:87]
                amount = Decimal(f"{whole_number_part}.{fractional_part}")

                # Arvopäivä
                value_date_str = line[21:27]
                # Kirjauspäivä
                date_of_entry_str = line[15:21]
                payment_date = self.get_payment_date(
                    value_date_str, date_of_entry_str, invoice_number
                )
                if payment_date is None:
                    self.stderr.write(
                        f"  Skipped row: malformed value_date and date_of_entry in payment row: "
                        f"{invoice_number} {value_date_str} {date_of_entry_str}."
                    )
                    continue

                self.stdout.write(
                    f" Invoice #{invoice_number} amount: {amount} date: {payment_date} filing code: {filing_code}"
                )

                try:
                    invoice = Invoice.objects.get(number=invoice_number)
                except Invoice.DoesNotExist:
                    self.stderr.write(
                        f'  Skipped row: invoice number "{invoice_number}" does not exist.'
                    )
                    continue

                lease: Lease = invoice.lease
                if lease.is_subject_to_vat:
                    vat: Optional[Vat] = invoice.get_vat_if_subject_to_vat(
                        payment_date, amount
                    )

                    if not vat:
                        self.stdout.write(
                            f"  Lease is subject to VAT but no VAT percent found for payment date {payment_date} or \
billing_period_end_date {invoice.billing_period_end_date} !"
                        )
                        continue

                    amount_without_vat = vat.calculate_amount_without_vat(amount)

                    self.stdout.write(
                        f"  Lease is subject to VAT. Amount: amount - VAT {vat.percent}% = {amount_without_vat}"
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
