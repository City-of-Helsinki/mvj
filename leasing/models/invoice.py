from xml.etree import ElementTree

from django.db import models
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumField

from leasing.enums import InvoiceState
from leasing.models import Contact
from leasing.models.mixins import TimestampedModelMixin


def get_laske_value(name):
    from django.conf import settings

    if not hasattr(settings, 'LASKE_VALUES'):
        return ''

    return getattr(settings, 'LASKE_VALUES').get(name, '')


class Invoice(TimestampedModelMixin):
    tenants = models.ManyToManyField('leasing.Tenant')
    note = models.CharField(verbose_name=_("Note"), null=True, blank=True, max_length=2048)
    period_start_date = models.DateField(verbose_name=_("Period start date"), null=True, blank=True)
    period_end_date = models.DateField(verbose_name=_("Period end date"), null=True, blank=True)
    due_date = models.DateField(verbose_name=_("Due date"), null=True, blank=True)
    amount = models.DecimalField(verbose_name=_("Amount"), max_digits=6, decimal_places=2)
    reference_number = models.CharField(verbose_name=_("Reference number"), null=True, blank=True, max_length=2048)
    billing_contact = models.ForeignKey('leasing.Contact', related_name="invoice_billing_contacts", null=True,
                                        blank=True, on_delete=models.PROTECT)
    state = EnumField(InvoiceState, verbose_name=_("State"), max_length=255,
                      default=InvoiceState.PENDING)

    def create_reference_number(self):
        if not self.id:
            return None

        reference_number = '91112{}880'.format(self.id)

        reversed_digits = reversed(str(reference_number))
        checksum = -sum((7, 3, 1)[i % 3] * int(x) for (i, x) in enumerate(reversed_digits)) % 10
        self.reference_number = reference_number + str(checksum)

        self.save()

    def get_laske_bill_text_elements(self):
        elements = []

        lease = self.tenants.first().lease

        bill_text_l1 = ElementTree.Element('BillTextL1')
        bill_text_l1.text = 'Vuokraustunnus: {}  Vuokra ajalta: {}-{}'.format(
            lease.identifier_string(),
            self.period_start_date.strftime('%d.%m.%Y'),
            self.period_end_date.strftime('%d.%m.%Y'),
        )
        elements.append(bill_text_l1)

        bill_text_l2 = ElementTree.Element('BillTextL2')
        bill_text_l2.text = 'Sopimuksen päättymispvm: {}'.format(
            lease.end_date.strftime('%d.%m.%Y') if lease.end_date else '-'
        )
        elements.append(bill_text_l2)

        bill_text_l3 = ElementTree.Element('BillTextL3')
        bill_text_l3.text = 'Käyttötarkoitus: TODO'
        elements.append(bill_text_l3)

        bill_text_l4 = ElementTree.Element('BillTextL4')
        bill_text_l4.text = 'Indeksin tark.pvm: -  Vuosivuokra: {}'.format(
            lease.get_year_rent()
        )
        elements.append(bill_text_l4)

        bill_text_l5 = ElementTree.Element('BillTextL5')
        bill_text_l5.text = 'Kiinteistötunnus: {}'.format(
            ', '.join(lease.get_real_property_unit_identifiers())
        )
        elements.append(bill_text_l5)

        bill_text_l6 = ElementTree.Element('BillTextL6')
        bill_text_l6.text = 'Vuokrakohteen osoite: {}'.format(
            ', '.join(lease.get_real_property_unit_addresses())
        )
        elements.append(bill_text_l6)

        return elements

    def get_laske_parties(self):
        elements = []

        if self.billing_contact:
            elements.append(self.billing_contact.as_laske_xml('OrderParty'))
            elements.append(self.billing_contact.as_laske_xml('BillingParty1'))
            elements.append(Contact().as_laske_xml('BillingParty2'))
            elements.append(self.billing_contact.as_laske_xml('PayerParty'))
        else:
            elements.append(Contact().as_laske_xml('OrderParty'))
            elements.append(Contact().as_laske_xml('BillingParty1'))
            elements.append(Contact().as_laske_xml('BillingParty2'))
            elements.append(Contact().as_laske_xml('PayerParty'))

        return elements

    def get_laske_line_item(self):
        line_item = ElementTree.Element('LineItem')

        ElementTree.SubElement(line_item, 'GroupingFactor')
        material = ElementTree.SubElement(line_item, 'Material')
        material.text = 'TODO'
        ElementTree.SubElement(line_item, 'MaterialDescription')
        quantity = ElementTree.SubElement(line_item, 'Quantity')
        quantity.text = '1,00'
        ElementTree.SubElement(line_item, 'Unit')
        net_price = ElementTree.SubElement(line_item, 'NetPrice')
        net_price.text = '{:.2f}'.format(self.amount).replace('.', ',')
        line_text_l1 = ElementTree.SubElement(line_item, 'LineTextL1')

        lease = self.tenants.first().lease
        lease_tenants = set(lease.tenants.all())
        invoice_tenants = set(self.tenants.all())

        if lease_tenants.difference(invoice_tenants):
            names = [str(tenant.contact) for tenant in lease_tenants.difference(invoice_tenants)]
            line_text_l1.text = 'Muita vuokraajia : {}'.format(', '.join(names))

        ElementTree.SubElement(line_item, 'LineTextL2')
        ElementTree.SubElement(line_item, 'LineTextL3')
        line_text_l4 = ElementTree.SubElement(line_item, 'LineTextL4')
        line_text_l4.text = '   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä.'
        line_text_l5 = ElementTree.SubElement(line_item, 'LineTextL5')
        line_text_l5.text = ' Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja'.format()
        line_text_l6 = ElementTree.SubElement(line_item, 'LineTextL6')
        line_text_l6.text = ' mahdollisista perimistoimenpiteistä perimispalkkio.'.format()
        ElementTree.SubElement(line_item, 'ProfitCenter')
        order_item_number = ElementTree.SubElement(line_item, 'OrderItemNumber')
        order_item_number.text = 'TODO'
        ElementTree.SubElement(line_item, 'WBS_Element')
        ElementTree.SubElement(line_item, 'FunctionalArea')
        ElementTree.SubElement(line_item, 'BusinessEntity')
        ElementTree.SubElement(line_item, 'Building')
        ElementTree.SubElement(line_item, 'RentalObject')

        return line_item

    def as_laske_xml(self):
        lease = self.tenants.first().lease

        root = ElementTree.Element('SBO_SalesOrder')
        sender_id = ElementTree.SubElement(root, 'SenderId')
        sender_id.text = get_laske_value('SenderId')
        reference = ElementTree.SubElement(root, 'Reference')
        if self.reference_number:
            reference.text = self.reference_number
        ElementTree.SubElement(root, 'OriginalOrder')
        contract_number = ElementTree.SubElement(root, 'ContractNumber')
        contract_number.text = lease.get_contract_number()
        order_type = ElementTree.SubElement(root, 'OrderType')
        order_type.text = get_laske_value('OrderType')
        sales_org = ElementTree.SubElement(root, 'SalesOrg')
        sales_org.text = get_laske_value('SalesOrg')
        distribution_channel = ElementTree.SubElement(root, 'distribution_channel')
        distribution_channel.text = get_laske_value('distribution_channel')
        division = ElementTree.SubElement(root, 'Division')
        division.text = get_laske_value('Division')
        sales_office = ElementTree.SubElement(root, 'SalesOffice')
        sales_office.text = get_laske_value('SalesOffice')
        ElementTree.SubElement(root, 'SalesGroup')
        ElementTree.SubElement(root, 'PONumber')
        ElementTree.SubElement(root, 'BillingBlock')
        ElementTree.SubElement(root, 'SalesDistrict')
        ElementTree.SubElement(root, 'HiddenTextL1')
        ElementTree.SubElement(root, 'HiddenTextL2')
        ElementTree.SubElement(root, 'HiddenTextL3')
        ElementTree.SubElement(root, 'HiddenTextL4')
        ElementTree.SubElement(root, 'HiddenTextL5')
        ElementTree.SubElement(root, 'HiddenTextL6')

        root.extend(self.get_laske_bill_text_elements())

        ElementTree.SubElement(root, 'ReferenceText')
        pmntterm = ElementTree.SubElement(root, 'PMNTTERM')
        pmntterm.text = get_laske_value('PMNTTERM')
        ElementTree.SubElement(root, 'OrderReason')
        billing_date = ElementTree.SubElement(root, 'BillingDate')
        billing_date.text = self.created_at.strftime('%Y%m%d')
        ElementTree.SubElement(root, 'PricingDate')
        value_date = ElementTree.SubElement(root, 'ValueDate')
        value_date.text = self.created_at.strftime('%Y%m%d')
        ElementTree.SubElement(root, 'PaymentReference')
        ElementTree.SubElement(root, 'AlreadyPrintedFlag')

        root.extend(self.get_laske_parties())
        root.append(self.get_laske_line_item())

        return root
