import cx_Oracle  # isort:skip (Not installed in CI or production)

from leasing.models import Invoice

from .base import BaseImporter
from .utils import rows_to_dict_list


class InvoiceRelationsImporter(BaseImporter):
    type_name = 'invoice_relations'

    def __init__(self, stdout=None, stderr=None):
        connection = cx_Oracle.connect(user='mvj', password='mvjpass', dsn='localhost:1521/ORCLPDB1', encoding="UTF-8",
                                       nencoding="UTF-8")

        self.cursor = connection.cursor()
        self.stdout = stdout
        self.stderr = stderr

    @classmethod
    def add_arguments(cls, parser):
        pass

    def read_options(self, options):
        pass

    def execute(self):
        from auditlog.registry import auditlog

        # Unregister all models from auditlog when importing
        for model in list(auditlog._registry.keys()):
            auditlog.unregister(model)

        self.update_credit_notes()
        self.update_interest_invoices()

    def update_credit_notes(self):
        cursor = self.cursor

        self.stdout.write('Updating credit notes:')

        query = """
            SELECT *
            FROM R_LASKU_HYVITYSLASKU"""

        cursor.execute(query)
        rows = rows_to_dict_list(cursor)

        for row in rows:
            try:
                credited_invoice = Invoice.objects.get(number=row['LASKU'])
            except Invoice.DoesNotExist:
                self.stdout.write("Credited invoice number #{} does not exist".format(row['LASKU']))
                continue
            except Invoice.MultipleObjectsReturned:
                self.stdout.write("Multiple invoices returned for Credited invoice number #{}!".format(
                    row['LASKU']))
                continue

            try:
                credit_note = Invoice.objects.get(number=row['HYVITYSLASKU'])
            except Invoice.DoesNotExist:
                self.stdout.write("Credit invoice number #{} does not exist".format(row['HYVITYSLASKU']))
                continue
            except Invoice.MultipleObjectsReturned:
                self.stdout.write("Multiple invoices returned for credit invoice number #{}!".format(
                    row['HYVITYSLASKU']))
                continue

            self.stdout.write("{} credits {}".format(credit_note.id, credited_invoice.id))

            credit_note.credited_invoice = credited_invoice
            credit_note.save()

    def update_interest_invoices(self):
        cursor = self.cursor

        self.stdout.write('Updating interest invoices:')

        query = """
            SELECT *
            FROM R_LASKU_KORKOLASKU"""

        cursor.execute(query)
        rows = rows_to_dict_list(cursor)

        for row in rows:
            try:
                invoice = Invoice.objects.get(number=row['LASKU'])
            except Invoice.DoesNotExist:
                self.stdout.write("Invoice number #{} does not exist".format(row['LASKU']))
                continue
            except Invoice.MultipleObjectsReturned:
                self.stdout.write("Multiple invoices returned for invoice number #{}!".format(row['LASKU']))
                continue

            try:
                interest_invoice = Invoice.objects.get(number=row['KORKOLASKU'])
            except Invoice.DoesNotExist:
                self.stdout.write("Interest invoice number #{} does not exist".format(row['KORKOLASKU']))
                continue
            except Invoice.MultipleObjectsReturned:
                self.stdout.write("Multiple invoices returned for interest invoice number #{}!".format(
                    row['HYVITYSLASKU']))
                continue

            interest_invoice.interest_invoice_for = invoice
            interest_invoice.save()

            self.stdout.write("{} is an interest invoice for {}".format(interest_invoice.id, invoice.id))
