import calendar
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from auditlog.registry import auditlog
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from enumfields import EnumField
from sequences import get_next_value

from field_permissions.registry import field_permissions
from leasing.enums import InvoiceDeliveryMethod, InvoiceState, InvoiceType
from leasing.models import Contact
from leasing.models.mixins import TimeStampedSafeDeleteModel
from leasing.models.utils import get_next_business_day, get_range_overlap


class ReceivableType(models.Model):
    """
    In Finnish: Saamislaji
    """

    name = models.CharField(verbose_name=_("Name"), max_length=255)
    sap_material_code = models.CharField(
        verbose_name=_("SAP material code"), null=True, blank=True, max_length=255
    )
    sap_order_item_number = models.CharField(
        verbose_name=_("SAP order item number"), null=True, blank=True, max_length=255
    )
    is_active = models.BooleanField(verbose_name=_("Is active?"), default=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Receivable type")
        verbose_name_plural = pgettext_lazy("Model name", "Receivable types")

    def __str__(self):
        return self.name


class InvoiceSet(models.Model):
    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="invoicesets",
        on_delete=models.PROTECT,
    )
    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(
        verbose_name=_("Billing period start date"), null=True, blank=True
    )

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(
        verbose_name=_("Billing period end date"), null=True, blank=True
    )

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice set")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice set")

    def create_credit_invoiceset(self, receivable_type=None, notes=""):
        all_invoices = self.invoices.filter(type=InvoiceType.CHARGE)

        if not all_invoices:
            raise RuntimeError(
                'No refundable invoices found (no invoices with the type "{}" found)'.format(
                    InvoiceType.CHARGE.value
                )
            )

        credit_invoiceset = InvoiceSet.objects.create(
            lease=self.lease,
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date,
        )

        for invoice in all_invoices:
            credit_invoice = invoice.create_credit_invoice(
                receivable_type=receivable_type, notes=notes
            )
            if credit_invoice:
                credit_invoiceset.invoices.add(credit_invoice)

        return credit_invoiceset

    def create_credit_invoiceset_for_amount(
        self, amount=None, receivable_type=None, notes=""
    ):
        if amount and not receivable_type:
            raise RuntimeError("receivable_type is required if amount is provided.")

        all_invoices = self.invoices.filter(type=InvoiceType.CHARGE)

        if not all_invoices:
            raise RuntimeError(
                'No refundable invoices found (no invoices with the type "{}" found)'.format(
                    InvoiceType.CHARGE.value
                )
            )

        shares = {}
        all_shares = Fraction()

        total_row_count = InvoiceRow.objects.filter(
            invoice__in=all_invoices, receivable_type=receivable_type
        ).count()

        has_tenants = (
            InvoiceRow.objects.filter(
                invoice__in=all_invoices,
                receivable_type=receivable_type,
                tenant__isnull=False,
            ).count()
            == total_row_count
        )

        total_row_amount = InvoiceRow.objects.filter(
            invoice__in=all_invoices, receivable_type=receivable_type
        ).aggregate(total_row_amount=Sum("amount"))["total_row_amount"]

        if amount > total_row_amount:
            raise RuntimeError(
                'Credit amount "{}" is more that total row amount "{}"!'.format(
                    amount, total_row_amount
                )
            )

        for invoice in all_invoices:
            if has_tenants:
                shares[invoice] = invoice.get_fraction_for_receivable_type(
                    receivable_type
                )
            else:
                shares[invoice] = Fraction(
                    invoice.rows.filter(receivable_type=receivable_type).count(),
                    total_row_count,
                )

            all_shares += shares[invoice]

        if all_shares != 1:
            raise RuntimeError("Shares together do not equal 1/1")

        credit_invoiceset = InvoiceSet.objects.create(
            lease=self.lease,
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date,
        )

        total_credited_amount = Decimal(0)

        for i, (invoice, fraction) in enumerate(shares.items()):
            invoice_credit_amount = Decimal(
                amount * Decimal(fraction.numerator / fraction.denominator)
            ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
            total_credited_amount += invoice_credit_amount

            # If this is the last share, check if we need to round
            if i == len(shares) - 1 and total_credited_amount.compare(
                amount
            ) != Decimal("0"):
                invoice_credit_amount += amount - total_credited_amount

            credit_invoice = invoice.create_credit_invoice(
                amount=invoice_credit_amount,
                receivable_type=receivable_type,
                notes=notes,
            )
            credit_invoiceset.invoices.add(credit_invoice)

        return credit_invoiceset


class Invoice(TimeStampedSafeDeleteModel):
    """
    In Finnish: Lasku
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="invoices",
        on_delete=models.PROTECT,
    )

    invoiceset = models.ForeignKey(
        InvoiceSet,
        verbose_name=_("Invoice set"),
        related_name="invoices",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Laskun numero
    number = models.PositiveIntegerField(
        verbose_name=_("Number"), unique=True, null=True, blank=True
    )

    # In Finnish: Laskunsaaja
    recipient = models.ForeignKey(
        Contact, verbose_name=_("Recipient"), related_name="+", on_delete=models.PROTECT
    )

    # In Finnish: Lähetetty SAP:iin
    sent_to_sap_at = models.DateTimeField(
        verbose_name=_("Sent to SAP at"), null=True, blank=True
    )

    # In Finnish: SAP numero
    sap_id = models.CharField(
        verbose_name=_("SAP ID"), max_length=255, null=True, blank=True
    )

    # In Finnish: Eräpäivä
    due_date = models.DateField(verbose_name=_("Due date"))

    # In Finnish: Eräpäivä (siirretty)
    # Used in Laske export ValueDate calculation if due_date is on a banking holiday
    adjusted_due_date = models.DateField(
        verbose_name=_("Adjusted due date"), null=True, blank=True
    )

    # In Finnish: Laskutuspvm
    invoicing_date = models.DateField(
        verbose_name=_("Invoicing date"), null=True, blank=True
    )

    # In Finnish: Laskun tila
    state = EnumField(InvoiceState, verbose_name=_("State"), max_length=30)

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(
        verbose_name=_("Billing period start date"), null=True, blank=True
    )

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(
        verbose_name=_("Billing period end date"), null=True, blank=True
    )

    # In Finnish: Lykkäyspvm
    postpone_date = models.DateField(
        verbose_name=_("Postpone date"), null=True, blank=True
    )

    # In Finnish: Laskun pääoma
    # TODO: Remove column and calculate total on-the-fly
    total_amount = models.DecimalField(
        verbose_name=_("Total amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Laskutettu määrä
    billed_amount = models.DecimalField(
        verbose_name=_("Billed amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Maksamaton määrä
    outstanding_amount = models.DecimalField(
        verbose_name=_("Outstanding amount"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Maksukehotuspvm
    payment_notification_date = models.DateField(
        verbose_name=_("Payment notification date"), null=True, blank=True
    )

    # In Finnish: Perintäkulu
    collection_charge = models.DecimalField(
        verbose_name=_("Collection charge"),
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
    )

    # In Finnish: Maksukehotus luettelo
    payment_notification_catalog_date = models.DateField(
        verbose_name=_("Payment notification catalog date"), null=True, blank=True
    )

    # In Finnish: E vai paperilasku
    delivery_method = EnumField(
        InvoiceDeliveryMethod,
        verbose_name=_("Delivery method"),
        max_length=30,
        null=True,
        blank=True,
    )

    # In Finnish: Laskun tyyppi
    type = EnumField(InvoiceType, verbose_name=_("Type"), max_length=30)

    # In Finnish: Tiedote
    notes = models.TextField(verbose_name=_("Notes"), blank=True)

    generated = models.BooleanField(
        verbose_name=_("Is automatically generated?"), default=False
    )

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Hyvitetty lasku
    credited_invoice = models.ForeignKey(
        "self",
        verbose_name=_("Credited invoice"),
        related_name="credit_invoices",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Korko laskulle
    interest_invoice_for = models.ForeignKey(
        "self",
        verbose_name=_("Interest invoice for"),
        related_name="interest_invoices",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Palvelukokonaisuus
    service_unit = models.ForeignKey(
        "leasing.ServiceUnit",
        verbose_name=_("Service unit"),
        related_name="invoices",
        on_delete=models.PROTECT,
    )

    recursive_get_related_skip_relations = [
        "lease",
        "laskeexportlog",
        "laskeexportloginvoiceitem",
    ]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice")
        verbose_name_plural = pgettext_lazy("Model name", "Invoices")

    def __str__(self):
        return str(self.pk)

    def get_service_unit(self):
        return self.service_unit

    def delete(self, force_policy=None, **kwargs):
        super().delete(force_policy=force_policy, **kwargs)

        if self.invoiceset:
            other_invoice = (
                self.invoiceset.invoices.filter(type=self.type, deleted__isnull=True)
                .exclude(id=self.id)
                .first()
            )
            if other_invoice:
                other_invoice.update_amounts()

    def update_amounts(self):
        rows_sum = self.rows.aggregate(sum=Sum("amount"))["sum"]
        if not rows_sum:
            rows_sum = Decimal(0)

        self.billed_amount = rows_sum

        if not self.invoiceset:
            self.total_amount = rows_sum
        else:
            # Sum amounts from all of the rows in the same type of invoices in this invoiceset
            invoiceset_rows_sum = InvoiceRow.objects.filter(
                invoice__invoiceset=self.invoiceset,
                invoice__type=self.type,
                invoice__deleted__isnull=True,
                deleted__isnull=True,
            ).aggregate(sum=Sum("amount"))["sum"]
            if not invoiceset_rows_sum:
                invoiceset_rows_sum = Decimal(0)

            # Update sum to all of the same type invoices in this invoiceset
            self.invoiceset.invoices.filter(
                type=self.type, deleted__isnull=True
            ).exclude(id=self.id).update(total_amount=invoiceset_rows_sum)

            # Need to set self total_amount separately because the
            # total_amount is not automatically refreshed from the
            # database
            self.total_amount = invoiceset_rows_sum

        payments_total = self.payments.aggregate(sum=Sum("paid_amount"))["sum"]
        if not payments_total:
            payments_total = Decimal(0)

        # Aggregating like this ignores the manager (i.e. includes deleted rows which we don't want):
        # total_credited_amount = self.credit_invoices.aggregate(sum=Sum("rows__amount"))["sum"]
        # ... so we have to iterate the rows and tally the sum by hand
        total_credited_amount = Decimal(0)
        for credit_inv in self.credit_invoices.all():
            for row in credit_inv.rows.all():
                total_credited_amount += row.amount

        collection_charge = Decimal(0)
        if self.collection_charge:
            collection_charge = self.collection_charge

        self.outstanding_amount = max(
            Decimal(0),
            self.billed_amount
            + collection_charge
            - payments_total
            - total_credited_amount,
        )
        # Don't mark as refunded unless credited amount is nonzero
        if total_credited_amount != Decimal(0) and total_credited_amount.compare(
            self.billed_amount
        ) != Decimal(-1):
            self.state = InvoiceState.REFUNDED
        elif self.type == InvoiceType.CHARGE and self.outstanding_amount == Decimal(0):
            self.state = InvoiceState.PAID

        self.save()

    def create_credit_invoice(  # noqa C901 TODO
        self, row_ids=None, amount=None, receivable_type=None, notes=""
    ):
        """Create a credit note for this invoice"""
        if self.type != InvoiceType.CHARGE:
            raise RuntimeError(
                'Can not credit invoice with the type "{}". Only type "{}" allowed.'.format(
                    self.type.value if self.type else self.type,
                    InvoiceType.CHARGE.value,
                )
            )

        row_queryset = self.rows.all()
        if row_ids:
            row_queryset = row_queryset.filter(id__in=row_ids)

        if receivable_type:
            row_queryset = row_queryset.filter(receivable_type=receivable_type)

        row_count = row_queryset.count()

        if not row_count:
            raise RuntimeError("No rows to credit")

        total_row_amount = row_queryset.aggregate(sum=Sum("amount"))["sum"]

        previously_credited_amount = InvoiceRow.objects.filter(
            invoice__in=self.credit_invoices.all(),
            receivable_type_id__in=[r.receivable_type for r in row_queryset.all()],
        ).aggregate(sum=Sum("amount"))["sum"]

        if not previously_credited_amount:
            previously_credited_amount = Decimal(0)

        if amount:
            if total_row_amount.compare(amount) == Decimal(-1):
                raise RuntimeError("Cannot credit more than invoice row amount")

            non_credited_amount = total_row_amount - previously_credited_amount

            if non_credited_amount.compare(amount) == Decimal(-1):
                raise RuntimeError(
                    "Cannot credit more than total amount minus already credited amount"
                )
        elif previously_credited_amount:
            # If crediting fully but there are previous credits, use the remaining amount
            amount = total_row_amount - previously_credited_amount

        has_tenants = row_queryset.filter(tenant__isnull=False).count() == row_count

        new_denominator = None
        if has_tenants:
            new_denominator = row_queryset.aggregate(
                new_denominator=Sum("tenant__share_numerator")
            )["new_denominator"]

        today = timezone.now().date()

        credit_note = Invoice.objects.create(
            lease=self.lease,
            type=InvoiceType.CREDIT_NOTE,
            recipient=self.recipient,
            due_date=self.due_date,
            invoicing_date=today,
            state=InvoiceState.PAID,
            total_amount=Decimal(0),
            billed_amount=Decimal(0),
            billing_period_start_date=self.billing_period_start_date,
            billing_period_end_date=self.billing_period_end_date,
            credited_invoice=self,
            notes=notes,
        )

        total_credited_amount = Decimal(0)

        row_count = row_queryset.count()

        for i, invoice_row in enumerate(row_queryset):
            if amount:
                if has_tenants:
                    invoice_row_amount = Decimal(
                        amount
                        * Decimal(invoice_row.tenant.share_numerator / new_denominator)
                    ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                else:
                    invoice_row_amount = Decimal(amount) / row_count
            else:
                invoice_row_amount = invoice_row.amount

            total_credited_amount += invoice_row_amount

            # If this is the last row, check if we need to round
            if (
                amount
                and i == row_count - 1
                and total_credited_amount.compare(amount) != Decimal("0")
            ):
                difference = amount - total_credited_amount
                invoice_row_amount += difference
                total_credited_amount += difference

            InvoiceRow.objects.create(
                invoice=credit_note,
                tenant=invoice_row.tenant,
                receivable_type=invoice_row.receivable_type,
                billing_period_start_date=invoice_row.billing_period_start_date,
                billing_period_end_date=invoice_row.billing_period_end_date,
                amount=invoice_row_amount,
            )

        credit_note.total_amount = total_credited_amount
        credit_note.save()

        self.update_amounts()

        return credit_note

    def get_fraction_for_receivable_type(self, receivable_type):
        fraction = Fraction()
        for row in self.rows.all():
            if row.receivable_type != receivable_type or not row.tenant:
                continue

            fraction += Fraction(
                row.tenant.share_numerator, row.tenant.share_denominator
            )

        return fraction

    def calculate_penalty_interest(self, calculation_date=None):
        from .debt_collection import InterestRate

        penalty_interest_data = {
            "interest_start_date": None,
            "interest_end_date": None,
            "outstanding_amount": self.outstanding_amount,
            "total_interest_amount": Decimal(0),
            "interest_periods": [],
        }
        if not calculation_date:
            calculation_date = timezone.now().date()

        if not self.outstanding_amount:
            return penalty_interest_data

        interest_start_date = get_next_business_day(self.due_date)
        interest_end_date = calculation_date

        penalty_interest_data["interest_start_date"] = interest_start_date
        penalty_interest_data["interest_end_date"] = interest_end_date

        years = range(interest_start_date.year, interest_end_date.year + 1)

        total_interest_amount = Decimal(0)

        for interest_rate in InterestRate.objects.filter(
            start_date__year__in=years
        ).order_by("start_date"):
            overlap = get_range_overlap(
                interest_rate.start_date,
                interest_rate.end_date,
                interest_start_date,
                interest_end_date,
            )
            if not overlap or not overlap[0] or not overlap[1]:
                continue

            days_between = (overlap[1] - overlap[0]).days + 1  # Inclusive

            # TODO: which divisor to use
            # divisor = 360
            if calendar.isleap(interest_rate.start_date.year):
                divisor = 366
            else:
                divisor = 365

            interest_amount = (
                self.outstanding_amount
                * (interest_rate.penalty_rate / 100)
                / divisor
                * days_between
            )

            penalty_interest_data["interest_periods"].append(
                {
                    "start_date": overlap[0],
                    "end_date": overlap[1],
                    "penalty_rate": interest_rate.penalty_rate,
                    "interest_amount": interest_amount,
                }
            )

            total_interest_amount += interest_amount

        penalty_interest_data["total_interest_amount"] = total_interest_amount.quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )

        return penalty_interest_data

    def is_same_recipient_and_tenants(self, invoice):
        """Checks that the self and dict of invoice data have the same recipients
        and the same tenants on the rows."""
        assert isinstance(invoice, Invoice) or isinstance(invoice, dict)

        if isinstance(invoice, Invoice):
            invoice_as_dict = {
                "lease": invoice.lease,
                "recipient": invoice.recipient,
                "rows": [],
            }

            for row in invoice.rows.all():
                invoice_as_dict["rows"].append({"tenant": row.tenant})

            invoice = invoice_as_dict

        if self.lease != invoice["lease"]:
            return False

        if self.recipient != invoice["recipient"]:
            return False

        self_rows = self.rows.all()
        invoice_rows = invoice["rows"]

        self_tenants = {row.tenant for row in self_rows}
        invoice_tenants = {row["tenant"] for row in invoice_rows}

        # TODO: check for tenantcontact?
        if self_tenants == invoice_tenants:
            return True

        return False

    def generate_number(self):
        if self.number:
            return self.number

        with transaction.atomic():
            self.number = get_next_value("invoice_numbers", initial_value=1000000)
            self.save()

        return self.number


class InvoiceNote(TimeStampedSafeDeleteModel):
    """
    In Finnish: Laskun tiedote
    """

    lease = models.ForeignKey(
        "leasing.Lease",
        verbose_name=_("Lease"),
        related_name="invoice_notes",
        on_delete=models.PROTECT,
    )

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(
        verbose_name=_("Billing period start date"), null=True, blank=True
    )

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(
        verbose_name=_("Billing period end date"), null=True, blank=True
    )

    # In Finnish: Tiedote
    notes = models.TextField(verbose_name=_("Notes"), blank=True)

    recursive_get_related_skip_relations = ["lease"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice note")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice notes")


class InvoiceRow(TimeStampedSafeDeleteModel):
    """
    In Finnish: Rivi laskulla
    """

    invoice = models.ForeignKey(
        Invoice,
        verbose_name=_("Invoice"),
        related_name="rows",
        on_delete=models.CASCADE,
    )

    # In Finnish: Vuokralainen
    tenant = models.ForeignKey(
        "leasing.Tenant",
        verbose_name=_("Tenant"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Saamislaji
    receivable_type = models.ForeignKey(
        ReceivableType,
        verbose_name=_("Receivable type"),
        related_name="+",
        on_delete=models.PROTECT,
    )

    # In Finnish: Käyttötarkoitus
    intended_use = models.ForeignKey(
        "leasing.RentIntendedUse",
        verbose_name=_("Intended use"),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # In Finnish: Laskutuskauden alkupvm
    billing_period_start_date = models.DateField(
        verbose_name=_("Billing period start date"), null=True, blank=True
    )

    # In Finnish: Laskutuskauden loppupvm
    billing_period_end_date = models.DateField(
        verbose_name=_("Billing period end date"), null=True, blank=True
    )

    # In Finnish: Selite
    description = models.TextField(verbose_name=_("Description"), null=True, blank=True)

    # In Finnish: Määrä
    amount = models.DecimalField(
        verbose_name=_("Amount"), max_digits=10, decimal_places=2
    )

    recursive_get_related_skip_relations = ["invoice"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice row")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice rows")


class InvoicePayment(TimeStampedSafeDeleteModel):
    """
    In Finnish: Maksusuoritus
    """

    invoice = models.ForeignKey(
        Invoice,
        verbose_name=_("Invoice"),
        related_name="payments",
        on_delete=models.CASCADE,
    )

    # In Finnish: Maksettu määrä
    paid_amount = models.DecimalField(
        verbose_name=_("Paid amount"), max_digits=10, decimal_places=2
    )

    # In Finnish: Maksettu pvm
    paid_date = models.DateField(verbose_name=_("Paid date"))

    # In Finnish: Arkistointitunnus
    filing_code = models.CharField(
        verbose_name=_("Name"), null=True, blank=True, max_length=35
    )

    recursive_get_related_skip_relations = ["invoice", "laskepaymentslog"]

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Invoice payment")
        verbose_name_plural = pgettext_lazy("Model name", "Invoice payments")


class BankHoliday(models.Model):
    day = models.DateField(verbose_name=_("Day"), unique=True, db_index=True)

    class Meta:
        verbose_name = pgettext_lazy("Model name", "Bank holiday")
        verbose_name_plural = pgettext_lazy("Model name", "Bank holidays")
        ordering = ("day",)

    def __str__(self):
        return str(self.day)


auditlog.register(Invoice)
auditlog.register(InvoiceNote)
auditlog.register(InvoiceRow)
auditlog.register(InvoicePayment)

field_permissions.register(Invoice, exclude_fields=["lease", "laskeexportlog"])
field_permissions.register(InvoiceNote, exclude_fields=["lease"])
field_permissions.register(InvoiceRow, exclude_fields=["invoice"])
field_permissions.register(InvoicePayment, exclude_fields=["invoice"])
