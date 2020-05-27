# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from django.conf import settings

from .models import Contact


def serialize_invoice(invoice):
    lease = invoice.tenants.first().lease

    root = ElementTree.Element("SBO_SalesOrder")
    sender_id = ElementTree.SubElement(root, "SenderId")
    sender_id.text = get_laske_value("SenderId")
    reference = ElementTree.SubElement(root, "Reference")
    if invoice.reference_number:
        reference.text = invoice.reference_number
    ElementTree.SubElement(root, "OriginalOrder")
    contract_number = ElementTree.SubElement(root, "ContractNumber")
    contract_number.text = lease.get_contract_number()
    order_type = ElementTree.SubElement(root, "OrderType")
    order_type.text = get_laske_value("OrderType")
    sales_org = ElementTree.SubElement(root, "SalesOrg")
    sales_org.text = get_laske_value("SalesOrg")
    distribution_channel = ElementTree.SubElement(root, "distribution_channel")
    distribution_channel.text = get_laske_value("distribution_channel")
    division = ElementTree.SubElement(root, "Division")
    division.text = get_laske_value("Division")
    sales_office = ElementTree.SubElement(root, "SalesOffice")
    sales_office.text = get_laske_value("SalesOffice")
    ElementTree.SubElement(root, "SalesGroup")
    ElementTree.SubElement(root, "PONumber")
    ElementTree.SubElement(root, "BillingBlock")
    ElementTree.SubElement(root, "SalesDistrict")
    ElementTree.SubElement(root, "HiddenTextL1")
    ElementTree.SubElement(root, "HiddenTextL2")
    ElementTree.SubElement(root, "HiddenTextL3")
    ElementTree.SubElement(root, "HiddenTextL4")
    ElementTree.SubElement(root, "HiddenTextL5")
    ElementTree.SubElement(root, "HiddenTextL6")

    root.extend(get_laske_bill_text_elements(invoice))

    ElementTree.SubElement(root, "ReferenceText")
    pmntterm = ElementTree.SubElement(root, "PMNTTERM")
    pmntterm.text = get_laske_value("PMNTTERM")
    ElementTree.SubElement(root, "OrderReason")
    billing_date = ElementTree.SubElement(root, "BillingDate")
    billing_date.text = invoice.created_at.strftime("%Y%m%d")
    ElementTree.SubElement(root, "PricingDate")
    value_date = ElementTree.SubElement(root, "ValueDate")
    value_date.text = invoice.created_at.strftime("%Y%m%d")
    ElementTree.SubElement(root, "PaymentReference")
    ElementTree.SubElement(root, "AlreadyPrintedFlag")

    root.extend(get_laske_parties(invoice))
    root.append(get_laske_line_item(invoice))

    return root


def get_laske_value(name):
    return getattr(settings, "LASKE_VALUES", {}).get(name, "")


def get_laske_bill_text_elements(invoice):
    elements = []

    lease = invoice.tenants.first().lease

    bill_text_l1 = ElementTree.Element("BillTextL1")
    bill_text_l1.text = "Vuokraustunnus: {}  Vuokra ajalta: {}-{}".format(
        lease.identifier_string(),
        invoice.period_start_date.strftime("%d.%m.%Y"),
        invoice.period_end_date.strftime("%d.%m.%Y"),
    )
    elements.append(bill_text_l1)

    bill_text_l2 = ElementTree.Element("BillTextL2")
    bill_text_l2.text = "Sopimuksen päättymispvm: {}".format(
        lease.end_date.strftime("%d.%m.%Y") if lease.end_date else "-"
    )
    elements.append(bill_text_l2)

    bill_text_l3 = ElementTree.Element("BillTextL3")
    bill_text_l3.text = "Käyttötarkoitus: TODO"
    elements.append(bill_text_l3)

    bill_text_l4 = ElementTree.Element("BillTextL4")
    bill_text_l4.text = "Indeksin tark.pvm: -  Vuosivuokra: {}".format(
        lease.get_year_rent()
    )
    elements.append(bill_text_l4)

    bill_text_l5 = ElementTree.Element("BillTextL5")
    bill_text_l5.text = "Kiinteistötunnus: {}".format(
        ", ".join(lease.get_real_property_unit_identifiers())
    )
    elements.append(bill_text_l5)

    bill_text_l6 = ElementTree.Element("BillTextL6")
    bill_text_l6.text = "Vuokrakohteen osoite: {}".format(
        ", ".join(lease.get_real_property_unit_addresses())
    )
    elements.append(bill_text_l6)

    return elements


def get_laske_parties(invoice):
    elements = []

    if invoice.billing_contact:
        elements.append(serialize_contact(invoice.billing_contact, "OrderParty"))
        elements.append(serialize_contact(invoice.billing_contact, "BillingParty1"))
        elements.append(serialize_contact(Contact(), "BillingParty2"))
        elements.append(serialize_contact(invoice.billing_contact, "PayerParty"))
    else:
        elements.append(serialize_contact(Contact(), "OrderParty"))
        elements.append(serialize_contact(Contact(), "BillingParty1"))
        elements.append(serialize_contact(Contact(), "BillingParty2"))
        elements.append(serialize_contact(Contact(), "PayerParty"))

    return elements


def serialize_contact(contact, tag_name):
    root = ElementTree.Element(tag_name)
    ElementTree.SubElement(root, "SAPCustomerID")
    ElementTree.SubElement(root, "CustomerID")
    customer_yid = ElementTree.SubElement(root, "CustomerYID")
    customer_yid.text = contact.organization_id if contact.organization_id else None
    ElementTree.SubElement(root, "CustomerOVT")
    ElementTree.SubElement(root, "TemporaryAddress1")
    ElementTree.SubElement(root, "TemporaryAddress2")
    ElementTree.SubElement(root, "TemporaryPOCode")
    ElementTree.SubElement(root, "TemporaryPOCity")
    ElementTree.SubElement(root, "TemporaryPOPostalcode")
    ElementTree.SubElement(root, "TemporaryCity")
    ElementTree.SubElement(root, "TemporaryPostalcode")
    priority_name1 = ElementTree.SubElement(root, "PriorityName1")
    if contact.organization_name:
        priority_name1.text = contact.organization_name
    elif contact.name:
        priority_name1.text = contact.name
    ElementTree.SubElement(root, "PriorityName2")
    ElementTree.SubElement(root, "PriorityName3")
    ElementTree.SubElement(root, "PriorityName4")
    priority_address1 = ElementTree.SubElement(root, "PriorityAddress1")
    if contact.organization_address:
        priority_address1.text = contact.organization_address
    elif contact.address:
        priority_address1.text = contact.address
    ElementTree.SubElement(root, "PriorityAddress2")
    ElementTree.SubElement(root, "PriorityPOCode")
    ElementTree.SubElement(root, "PriorityPOCity")
    ElementTree.SubElement(root, "PriorityPOPostalcode")
    ElementTree.SubElement(root, "PriorityCity")
    ElementTree.SubElement(root, "PriorityPostalcode")
    ElementTree.SubElement(root, "InfoCustomerID")
    info_customer_yid = ElementTree.SubElement(root, "InfoCustomerYID")
    info_customer_yid.text = (
        contact.organization_id if contact.organization_id else None
    )
    ElementTree.SubElement(root, "InfoCustomerOVT")
    info_name1 = ElementTree.SubElement(root, "InfoName1")
    if contact.organization_name:
        info_name1.text = contact.organization_name
    elif contact.name:
        info_name1.text = contact.name
    ElementTree.SubElement(root, "InfoName2")
    ElementTree.SubElement(root, "InfoName3")
    ElementTree.SubElement(root, "InfoName4")
    info_address1 = ElementTree.SubElement(root, "InfoAddress1")
    if contact.organization_address:
        info_address1.text = contact.organization_address
    elif contact.address:
        info_address1.text = contact.address
    ElementTree.SubElement(root, "InfoAddress2")
    ElementTree.SubElement(root, "InfoPOCode")
    ElementTree.SubElement(root, "InfoPOCity")
    ElementTree.SubElement(root, "InfoPOPostalcode")
    ElementTree.SubElement(root, "InfoCity")
    ElementTree.SubElement(root, "InfoPostalcode")

    return root


def get_laske_line_item(invoice):
    line_item = ElementTree.Element("LineItem")

    ElementTree.SubElement(line_item, "GroupingFactor")
    material = ElementTree.SubElement(line_item, "Material")
    material.text = "TODO"
    ElementTree.SubElement(line_item, "MaterialDescription")
    quantity = ElementTree.SubElement(line_item, "Quantity")
    quantity.text = "1,00"
    ElementTree.SubElement(line_item, "Unit")
    net_price = ElementTree.SubElement(line_item, "NetPrice")
    net_price.text = "{:.2f}".format(invoice.amount).replace(".", ",")
    line_text_l1 = ElementTree.SubElement(line_item, "LineTextL1")

    lease = invoice.tenants.first().lease
    lease_tenants = set(lease.tenants.all())
    invoice_tenants = set(invoice.tenants.all())

    if lease_tenants.difference(invoice_tenants):
        names = [
            str(tenant.contact) for tenant in lease_tenants.difference(invoice_tenants)
        ]
        line_text_l1.text = "Muita vuokraajia : {}".format(", ".join(names))

    ElementTree.SubElement(line_item, "LineTextL2")
    ElementTree.SubElement(line_item, "LineTextL3")
    line_text_l4 = ElementTree.SubElement(line_item, "LineTextL4")
    line_text_l4.text = (
        "   Maksun suorittaminen: Maksu on suoritettava viimeistään eräpäivänä."
    )
    line_text_l5 = ElementTree.SubElement(line_item, "LineTextL5")
    line_text_l5.text = (
        " Eräpäivän jälkeen peritään korkolain mukainen viivästyskorko ja".format()
    )
    line_text_l6 = ElementTree.SubElement(line_item, "LineTextL6")
    line_text_l6.text = " mahdollisista perimistoimenpiteistä perimispalkkio.".format()
    ElementTree.SubElement(line_item, "ProfitCenter")
    order_item_number = ElementTree.SubElement(line_item, "OrderItemNumber")
    order_item_number.text = "TODO"
    ElementTree.SubElement(line_item, "WBS_Element")
    ElementTree.SubElement(line_item, "FunctionalArea")
    ElementTree.SubElement(line_item, "BusinessEntity")
    ElementTree.SubElement(line_item, "Building")
    ElementTree.SubElement(line_item, "RentalObject")

    return line_item
