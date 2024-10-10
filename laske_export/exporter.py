import json
import logging
import os
import tempfile
from base64 import decodebytes

import paramiko
import pysftp
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from laske_export.document.invoice_sales_order_adapter import (
    invoice_sales_order_adapter_factory,
)
from laske_export.document.land_use_agreement_invoice_sales_order_adapter import (
    LandUseAgreementInvoiceSalesOrderAdapter,
)
from laske_export.document.sales_order import SalesOrder, SalesOrderContainer
from laske_export.enums import LaskeExportLogInvoiceStatus
from laske_export.models import LaskeExportLog, LaskeExportLogInvoiceItem
from leasing.enums import InvoiceType
from leasing.models import Invoice, ServiceUnit
from leasing.models.land_use_agreement import LandUseAgreementInvoice

logger = logging.getLogger(__name__)


def create_sales_order_with_laske_values(service_unit: ServiceUnit) -> SalesOrder:
    sales_order = SalesOrder()

    for key, val in settings.LASKE_VALUES.items():
        setattr(sales_order, key, val)

    sales_order.sender_id = service_unit.laske_sender_id
    sales_order.sales_org = service_unit.laske_sales_org
    return sales_order


class LaskeExporterError(Exception):
    pass


class LaskeExporter:
    def __init__(self, service_unit: ServiceUnit):
        self.message_output = None
        self.service_unit = service_unit
        self._check_export_directory()
        self._check_settings()

    def _check_export_directory(self):
        if not os.path.isdir(settings.LASKE_EXPORT_ROOT):
            raise LaskeExporterError(
                _('Directory "{}" does not exist. Please create it.').format(
                    settings.LASKE_EXPORT_ROOT
                )
            )

        try:
            fp = tempfile.TemporaryFile(dir=settings.LASKE_EXPORT_ROOT)
            fp.close()
        except PermissionError:
            raise LaskeExporterError(
                _('Can not create file in directory "{}".').format(
                    settings.LASKE_EXPORT_ROOT
                )
            )

    def _check_settings(self):
        if (
            not hasattr(settings, "LASKE_SERVERS")
            or "export" not in settings.LASKE_SERVERS
            or not settings.LASKE_SERVERS.get("export")
            or not settings.LASKE_SERVERS["export"].get("host")
            or not settings.LASKE_SERVERS["export"].get("username")
            or not settings.LASKE_SERVERS["export"].get("password")
        ):
            raise LaskeExporterError(_('LASKE_SERVERS["export"] settings missing'))

    def save_to_file(self, xml_string, filename):
        full_path = os.path.join(settings.LASKE_EXPORT_ROOT, filename)

        with open(full_path, "wb") as fp:
            fp.write(xml_string)

    def send(self, filename):
        # Add destination server host key
        if settings.LASKE_SERVERS["export"]["key_type"] == "ssh-ed25519":
            key = paramiko.ed25519key.Ed25519Key(
                data=decodebytes(settings.LASKE_SERVERS["export"]["key"])
            )
        elif "ecdsa" in settings.LASKE_SERVERS["export"]["key_type"]:
            key = paramiko.ecdsakey.ECDSAKey(
                data=decodebytes(settings.LASKE_SERVERS["export"]["key"])
            )
        else:
            key = paramiko.rsakey.RSAKey(
                data=decodebytes(settings.LASKE_SERVERS["export"]["key"])
            )

        hostkeys = paramiko.hostkeys.HostKeys()
        hostkeys.add(
            settings.LASKE_SERVERS["export"]["host"],
            settings.LASKE_SERVERS["export"]["key_type"],
            key,
        )

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = hostkeys
        # Or Disable key check:
        # cnopts.hostkeys = None

        with pysftp.Connection(
            settings.LASKE_SERVERS["export"]["host"],
            port=settings.LASKE_SERVERS["export"]["port"],
            username=settings.LASKE_SERVERS["export"]["username"],
            password=settings.LASKE_SERVERS["export"]["password"],
            cnopts=cnopts,
        ) as sftp:
            with sftp.cd(settings.LASKE_SERVERS["export"]["directory"]):
                sftp.put(os.path.join(settings.LASKE_EXPORT_ROOT, filename))

    def write_to_output(self, message):
        if not self.message_output:
            return

        self.message_output.write(message)

    def export_invoices(self, invoices: list[Invoice]) -> LaskeExportLog:
        """Export invoices as XML and send them to Laske SAP"""

        now = timezone.now()
        laske_export_log_entry = LaskeExportLog.objects.create(
            started_at=now, filename="", service_unit=self.service_unit
        )

        sales_orders = []
        log_invoices = []
        invoice_count = 0

        self.write_to_output("Going through {} invoices".format(len(invoices)))

        for invoice in invoices:
            invoice_log_item = LaskeExportLogInvoiceItem(
                invoice=invoice, laskeexportlog=laske_export_log_entry
            )
            log_invoices.append(invoice_log_item)

            try:
                self.write_to_output(" Invoice id {}".format(invoice.id))

                # If this invoice is a credit note, but the credited invoice has
                # not been sent to SAP, don't send the credit invoice either.
                # TODO This doesn't check if the credited invoice would be sent
                #   in this same export. Need to check if the SAP can handle it.
                if invoice.type == InvoiceType.CREDIT_NOTE and (
                    not invoice.credited_invoice
                    or not invoice.credited_invoice.sent_to_sap_at
                ):
                    if invoice.credited_invoice:
                        self.write_to_output(
                            " Not sending invoice id {} because the credited invoice (id {}) "
                            "has not been sent to SAP.".format(
                                invoice.id, invoice.credited_invoice.id
                            )
                        )
                    else:
                        self.write_to_output(
                            " Not sending invoice id {} because the credited invoice is unknown.".format(
                                invoice.id
                            )
                        )

                    continue

                if not invoice.invoicing_date:
                    invoice.invoicing_date = now.date()
                    invoice.save()

                sales_order = create_sales_order_with_laske_values(invoice.service_unit)

                adapter = invoice_sales_order_adapter_factory(
                    invoice=invoice,
                    sales_order=sales_order,
                    service_unit=self.service_unit,
                    fill_priority_and_info=self.service_unit.laske_fill_priority_and_info,
                )
                adapter.set_values()

                sales_order.validate()

                sales_orders.append(sales_order)

                invoice_count += 1

                self.write_to_output(
                    " Added invoice id {} as invoice number {}".format(
                        invoice.id, invoice.number
                    )
                )

                invoice_log_item.status = LaskeExportLogInvoiceStatus.SENT
            except ValidationError as err:
                self.write_to_output(
                    "Validation error occurred in #{} ({}) invoice. Errors: {}".format(
                        invoice.number, invoice.id, "; ".join(err.messages)
                    )
                )
                logger.warning(err, exc_info=True)
                invoice_log_item.status = LaskeExportLogInvoiceStatus.FAILED
                invoice_log_item.information = json.dumps(err.message_dict)
            finally:
                invoice_log_item.save()

        if invoice_count > 0:
            self.write_to_output(
                "Added {} invoices to the export".format(invoice_count)
            )

            sales_order_container = SalesOrderContainer()
            sales_order_container.sales_orders = sales_orders

            export_filename = "MTIL_IN_{}_{}_{:08}.xml".format(
                self.service_unit.laske_sender_id,
                self.service_unit.laske_sales_org,
                laske_export_log_entry.id,
            )
            laske_export_log_entry.filename = export_filename

            self.write_to_output("Export filename: {}".format(export_filename))

            xml_string = sales_order_container.to_xml_string()

            self.save_to_file(xml_string, export_filename)

            self.write_to_output("Sending...")

            self.send(export_filename)

            self.write_to_output("Done.")

            Invoice.objects.filter(id__in=[o.id for o in invoices]).update(
                sent_to_sap_at=now
            )

        # TODO: Log errors
        laske_export_log_entry.ended_at = timezone.now()
        laske_export_log_entry.is_finished = True
        laske_export_log_entry.save()

        return laske_export_log_entry

    def export_land_use_agreement_invoices(
        self, invoices: list[LandUseAgreementInvoice]
    ) -> LaskeExportLog:
        now = timezone.now()
        laske_export_log_entry = LaskeExportLog.objects.create(
            started_at=now, filename="", service_unit=self.service_unit
        )

        sales_orders: list[SalesOrder] = []
        log_invoices: list[LandUseAgreementInvoice] = []
        invoice_count = 0

        self.write_to_output(
            "Going through {} land use agreement invoices".format(len(invoices))
        )

        for invoice in invoices:
            self.write_to_output(" Land use agreement invoice id {}".format(invoice.id))

            sales_order = create_sales_order_with_laske_values(self.service_unit)

            adapter = LandUseAgreementInvoiceSalesOrderAdapter(
                invoice=invoice,
                sales_order=sales_order,
            )
            adapter.set_values()

            sales_orders.append(sales_order)
            log_invoices.append(invoice)

            invoice_count += 1

            self.write_to_output(
                " Added invoice id {} as invoice number {}".format(
                    invoice.id, invoice.number
                )
            )

        if invoice_count > 0:
            self.write_to_output(
                "Added {} invoices to the export".format(invoice_count)
            )

            sales_order_container = SalesOrderContainer()
            sales_order_container.sales_orders = sales_orders

            laske_export_log_entry.land_use_agreement_invoices.set(log_invoices)

            export_filename = "MTIL_IN_{}_{}_{:08}.xml".format(
                self.service_unit.laske_sender_id,
                self.service_unit.laske_sales_org,
                laske_export_log_entry.id,
            )
            laske_export_log_entry.filename = export_filename

            self.write_to_output("Export filename: {}".format(export_filename))

            xml_string = sales_order_container.to_xml_string()

            self.save_to_file(xml_string, export_filename)

            self.write_to_output("Sending...")

            self.send(export_filename)

            self.write_to_output("Done.")

            LandUseAgreementInvoice.objects.filter(
                id__in=[o.id for o in invoices]
            ).update(sent_to_sap_at=now)

        # TODO: Log errors
        laske_export_log_entry.ended_at = timezone.now()
        laske_export_log_entry.is_finished = True
        laske_export_log_entry.save()

        return laske_export_log_entry
