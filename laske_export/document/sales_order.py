from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import ugettext_lazy as _

from leasing.enums import ContactType

from .fields import Field, FieldGroup


class Party(FieldGroup):
    sap_customer_id = Field(name="SAPCustomerID", validators=[MaxLengthValidator(10)])
    customer_id = Field(name="CustomerID", validators=[MaxLengthValidator(11)])
    customer_yid = Field(name="CustomerYID", validators=[MaxLengthValidator(9)])
    customer_ovt = Field(name="CustomerOVT", validators=[MaxLengthValidator(18)])
    temporary_address1 = Field(
        name="TemporaryAddress1", validators=[MaxLengthValidator(35)]
    )
    temporary_address2 = Field(
        name="TemporaryAddress2", validators=[MaxLengthValidator(35)]
    )
    temporary_po_code = Field(
        name="TemporaryPOCode", validators=[MaxLengthValidator(35)]
    )
    temporary_po_city = Field(
        name="TemporaryPOCity", validators=[MaxLengthValidator(35)]
    )
    temporary_po_postalcode = Field(
        name="TemporaryPOPostalcode", validators=[MaxLengthValidator(9)]
    )
    temporary_city = Field(name="TemporaryCity", validators=[MaxLengthValidator(35)])
    temporary_postalcode = Field(
        name="TemporaryPostalcode", validators=[MaxLengthValidator(9)]
    )
    priority_name1 = Field(name="PriorityName1", validators=[MaxLengthValidator(35)])
    priority_name2 = Field(name="PriorityName2", validators=[MaxLengthValidator(35)])
    priority_name3 = Field(name="PriorityName3", validators=[MaxLengthValidator(35)])
    priority_name4 = Field(name="PriorityName4", validators=[MaxLengthValidator(35)])
    priority_address1 = Field(
        name="PriorityAddress1", validators=[MaxLengthValidator(35)]
    )
    priority_address2 = Field(
        name="PriorityAddress2", validators=[MaxLengthValidator(35)]
    )
    priority_po_code = Field(name="PriorityPOCode", validators=[MaxLengthValidator(35)])
    priority_po_city = Field(name="PriorityPOCity", validators=[MaxLengthValidator(35)])
    priority_po_postalcode = Field(
        name="PriorityPOPostalcode", validators=[MaxLengthValidator(9)]
    )
    priority_city = Field(name="PriorityCity", validators=[MaxLengthValidator(35)])
    priority_postalcode = Field(
        name="PriorityPostalcode", validators=[MaxLengthValidator(9)]
    )
    info_customer_id = Field(name="InfoCustomerID", validators=[MaxLengthValidator(11)])
    info_customer_yid = Field(
        name="InfoCustomerYID", validators=[MaxLengthValidator(9)]
    )
    info_customer_ovt = Field(
        name="InfoCustomerOVT", validators=[MaxLengthValidator(18)]
    )
    info_name1 = Field(name="InfoName1", validators=[MaxLengthValidator(35)])
    info_name2 = Field(name="InfoName2", validators=[MaxLengthValidator(35)])
    info_name3 = Field(name="InfoName3", validators=[MaxLengthValidator(35)])
    info_name4 = Field(name="InfoName4", validators=[MaxLengthValidator(35)])
    info_address1 = Field(name="InfoAddress1", validators=[MaxLengthValidator(35)])
    info_address2 = Field(name="InfoAddress2", validators=[MaxLengthValidator(35)])
    info_po_code = Field(name="InfoPOCode", validators=[MaxLengthValidator(35)])
    info_po_city = Field(name="InfoPOCity", validators=[MaxLengthValidator(35)])
    info_po_postalcode = Field(
        name="InfoPOPostalcode", validators=[MaxLengthValidator(9)]
    )
    info_city = Field(name="InfoCity", validators=[MaxLengthValidator(35)])
    info_postalcode = Field(name="InfoPostalcode", validators=[MaxLengthValidator(9)])

    def from_contact(self, contact):  # NOQA C901 'Party.from_contact' is too complex
        if not contact:
            raise ValidationError(_("Contact information cannot be null."))

        self.customer_ovt = contact.electronic_billing_address
        self.info_customer_ovt = contact.electronic_billing_address

        self.sap_customer_id = contact.sap_customer_number
        if contact.type == ContactType.PERSON:
            self.customer_id = contact.national_identification_number
            self.info_customer_id = contact.national_identification_number
        else:
            self.customer_yid = contact.business_id
            self.info_customer_yid = contact.business_id

        name = contact.get_name()[:140]  # PriorityName1-4 max length = 4 * 35 chars

        n = 1
        if not name:
            self.priority_name1 = ""
            self.info_name1 = ""
            n += 1
        else:
            for i in range(0, len(name), 35):
                name_text_line = name[i : i + 35]
                # If only one character would be inserted on a line (e.g. len(name) == 36), just skip it
                if len(name[i : i + 35]) == 1:
                    name_text_line = ""
                setattr(self, "priority_name{}".format(n), name_text_line)
                setattr(self, "info_name{}".format(n), name_text_line)
                n += 1

        # Add care of to the priority name overwriting part of the name if necessary
        if contact.care_of:
            care_of = "c/o {}".format(contact.care_of)

            if n == 5:
                n = 4

            for i in range(0, len(care_of), 35):
                care_of_text_line = care_of[i : i + 35]
                # As above, skip one character lines
                if len(care_of[i : i + 35]) == 1:
                    care_of_text_line = ""
                setattr(self, "priority_name{}".format(n), care_of_text_line)
                setattr(self, "info_name{}".format(n), care_of_text_line)
                n += 1
                if n >= 5:
                    break

        self.priority_address1 = contact.address[:35] if contact.address else ""
        self.priority_city = contact.city
        self.priority_postalcode = contact.postal_code
        self.info_address1 = contact.address[:35] if contact.address else ""
        self.info_city = contact.city
        self.info_postalcode = contact.postal_code


class OrderParty(Party):
    class Meta:
        element_name = "OrderParty"


class BillingParty1(Party):
    class Meta:
        element_name = "BillingParty1"


class BillingParty2(Party):
    class Meta:
        element_name = "BillingParty2"


class PayerParty(Party):
    class Meta:
        element_name = "PayerParty"


class ShipToParty(Party):
    class Meta:
        element_name = "ShipToParty"


class LineItem(FieldGroup):
    grouping_factor = Field(name="GroupingFactor", validators=[MaxLengthValidator(35)])
    material = Field(name="Material", validators=[MaxLengthValidator(18)])
    material_description = Field(
        name="MaterialDescription", validators=[MaxLengthValidator(40)]
    )
    quantity = Field(name="Quantity", validators=[MaxLengthValidator(13)])
    unit = Field(name="Unit", validators=[MaxLengthValidator(3)])
    net_price = Field(
        name="NetPrice", validators=[MaxLengthValidator(14)], required=True
    )
    tax_code = Field(name="TaxCode", validators=[MaxLengthValidator(1)])
    line_text_l1 = Field(name="LineTextL1", validators=[MaxLengthValidator(70)])
    line_text_l2 = Field(name="LineTextL2", validators=[MaxLengthValidator(70)])
    line_text_l3 = Field(name="LineTextL3", validators=[MaxLengthValidator(70)])
    line_text_l4 = Field(name="LineTextL4", validators=[MaxLengthValidator(70)])
    line_text_l5 = Field(name="LineTextL5", validators=[MaxLengthValidator(70)])
    line_text_l6 = Field(name="LineTextL6", validators=[MaxLengthValidator(70)])
    profit_center = Field(name="ProfitCenter", validators=[MaxLengthValidator(10)])
    order_item_number = Field(
        name="OrderItemNumber", validators=[MaxLengthValidator(12)]
    )
    wbs_element = Field(name="WBS_Element", validators=[MaxLengthValidator(16)])
    functional_area = Field(name="FunctionalArea", validators=[MaxLengthValidator(6)])
    business_entity = Field(name="BusinessEntity", validators=[MaxLengthValidator(8)])
    building = Field(name="Building", validators=[MaxLengthValidator(8)])
    rental_object = Field(name="RentalObject", validators=[MaxLengthValidator(8)])

    class Meta:
        element_name = "LineItem"


class SalesOrder(FieldGroup):
    sender_id = Field(
        name="SenderId", validators=[MaxLengthValidator(5)], required=True
    )
    reference = Field(name="Reference", validators=[MaxLengthValidator(10)])
    original_order = Field(name="OriginalOrder", validators=[MaxLengthValidator(10)])
    contract_number = Field(name="ContractNumber", validators=[MaxLengthValidator(11)])
    order_type = Field(
        name="OrderType", validators=[MaxLengthValidator(4)], required=True
    )
    sales_org = Field(
        name="SalesOrg", validators=[MaxLengthValidator(4)], required=True
    )
    distribution_channel = Field(
        name="DistributionChannel", validators=[MaxLengthValidator(2)], required=True
    )
    division = Field(name="Division", validators=[MaxLengthValidator(2)], required=True)
    sales_office = Field(
        name="SalesOffice", validators=[MaxLengthValidator(4)], required=True
    )
    sales_group = Field(name="SalesGroup", validators=[MaxLengthValidator(3)])
    po_number = Field(name="PONumber", validators=[MaxLengthValidator(35)])
    billing_block = Field(name="BillingBlock", validators=[MaxLengthValidator(4)])
    sales_district = Field(name="SalesDistrict", validators=[MaxLengthValidator(6)])
    hidden_text_l1 = Field(name="HiddenTextL1", validators=[MaxLengthValidator(70)])
    hidden_text_l2 = Field(name="HiddenTextL2", validators=[MaxLengthValidator(70)])
    hidden_text_l3 = Field(name="HiddenTextL3", validators=[MaxLengthValidator(70)])
    hidden_text_l4 = Field(name="HiddenTextL4", validators=[MaxLengthValidator(70)])
    hidden_text_l5 = Field(name="HiddenTextL5", validators=[MaxLengthValidator(70)])
    hidden_text_l6 = Field(name="HiddenTextL6", validators=[MaxLengthValidator(70)])
    bill_text_l1 = Field(name="BillTextL1", validators=[MaxLengthValidator(70)])
    bill_text_l2 = Field(name="BillTextL2", validators=[MaxLengthValidator(70)])
    bill_text_l3 = Field(name="BillTextL3", validators=[MaxLengthValidator(70)])
    bill_text_l4 = Field(name="BillTextL4", validators=[MaxLengthValidator(70)])
    bill_text_l5 = Field(name="BillTextL5", validators=[MaxLengthValidator(70)])
    bill_text_l6 = Field(name="BillTextL6", validators=[MaxLengthValidator(70)])
    reference_text = Field(name="ReferenceText", validators=[MaxLengthValidator(20)])
    pmntterm = Field(name="PMNTTERM", validators=[MaxLengthValidator(4)])
    order_reason = Field(name="OrderReason", validators=[MaxLengthValidator(3)])
    billing_date = Field(name="BillingDate", validators=[MaxLengthValidator(8)])
    pricing_date = Field(name="PricingDate", validators=[MaxLengthValidator(8)])
    value_date = Field(name="ValueDate", validators=[MaxLengthValidator(8)])
    payment_reference = Field(
        name="PaymentReference", validators=[MaxLengthValidator(30)]
    )
    already_printed_flag = Field(
        name="AlreadyPrintedFlag", validators=[MaxLengthValidator(1)]
    )

    # Sub elements
    order_party = Field(name="OrderParty", field_type=OrderParty)
    billing_party1 = Field(name="BillingParty1", field_type=BillingParty1)
    billing_party2 = Field(name="BillingParty2", field_type=BillingParty2)
    payer_party = Field(name="PayerParty", field_type=PayerParty)
    line_items = Field(name="LineItem", field_type=LineItem, many=True)

    class Meta:
        element_name = "SBO_SalesOrder"

    def set_bill_texts_from_string(self, text):
        for num, line in enumerate(text.split("\n"), start=1):
            if num > 6:
                break

            setattr(self, "bill_text_l{}".format(num), line[:70])


class SalesOrderContainer(FieldGroup):
    sales_orders = Field(field_type=SalesOrder, many=True, required=True)

    class Meta:
        element_name = "SBO_SalesOrderContainer"
