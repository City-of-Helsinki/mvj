import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

from laske_export.exporter import LaskeExporter
from leasing.models.land_use_agreement import LandUseAgreementInvoice


class Command(BaseCommand):
    help = "Send land use agreement invoices to Laske"

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        # noinspection PyBroadException
        try:
            exporter = LaskeExporter()
            exporter.message_output = self.stdout

            self.stdout.write("Finding unsent land use agreement invoices")

            land_use_agreement_invoices = LandUseAgreementInvoice.objects.filter(
                sent_to_sap_at__isnull=True,
            )
            self.stdout.write(
                "Found {} unsent land use agreement invoices".format(
                    land_use_agreement_invoices.count()
                )
            )

            if not land_use_agreement_invoices:
                self.stdout.write("No invoices to send. Exiting.")
                return

            # TODO: laske_export_log_entry_lua =
            exporter.export_land_use_agreement_invoices(land_use_agreement_invoices)
        except Exception as err:
            error_message = str(err)
            self.stdout.write(
                "An error occurred in the invoice exporting. Error: {}".format(
                    error_message
                )
            )
            logging.exception(err)

        # TODO: Send announce email?
