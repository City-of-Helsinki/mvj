from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from laske_export.document.custom_validators import validate_payment_reference
from leasing.enums import ContactType
from leasing.models.contact import Contact

from .fields import Field, FieldGroup


def normalize_short_lines(text: str) -> str:
    """
    If the given line would contain only a single non-whitespace character (e.g. ' 1'),
    return a longer string with a dot appended string (e.g. ' 1.') to avoid emitting a 1-char line.
    Note: Whitespace is not counted for the length.
    """
    if len(text.strip()) == 1:
        return f"{text}."
    if len(text.strip()) == 0:
        return ""
    return text


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

    def __init__(self, fill_priority_and_info=True):
        super().__init__()
        self.fill_priority_and_info = fill_priority_and_info

    def from_contact(self, contact: Contact | None):
        if not contact:
            raise ValidationError(_("Contact information cannot be null."))

        self._set_customer_identifiers(contact)

        if self.fill_priority_and_info:
            self._set_info_identifiers(contact)
            self._set_name_fields(contact)
            self._set_address_fields(contact)

    def _set_customer_identifiers(self, contact: Contact):
        """Set basic customer identification fields."""
        self.customer_ovt = contact.electronic_billing_address
        self.sap_customer_id = contact.sap_customer_number

        if contact.type == ContactType.PERSON:
            self.customer_id = contact.national_identification_number
        else:
            self.customer_yid = contact.business_id

    def _set_info_identifiers(self, contact: Contact):
        """Set info party identification fields."""
        self.info_customer_ovt = contact.electronic_billing_address

        if contact.type == ContactType.PERSON:
            self.info_customer_id = contact.national_identification_number
        else:
            self.info_customer_yid = contact.business_id

    def _set_name_fields(self, contact: Contact):
        """Set priority and info name fields, including care_of if present."""
        name = contact.get_name()[:140]  # Max 4 * 35 chars
        line = self._write_name_lines(name)

        if contact.care_of:
            self._write_care_of_lines(contact.care_of, line)

    def _write_name_lines(self, name: str) -> int:
        """
        Write name across multiple priority/info name fields.
        Returns the next available line number.
        """
        line = 1

        if not name:
            self.priority_name1 = ""
            self.info_name1 = ""
            return 2

        for i in range(0, len(name), 35):
            name_text_line = normalize_short_lines(name[i : i + 35])
            setattr(self, f"priority_name{line}", name_text_line)
            setattr(self, f"info_name{line}", name_text_line)
            line += 1

        return line

    def _write_care_of_lines(self, care_of: str, start_line: int):
        """
        Write care_of information to priority/info name fields.
        May overwrite last name line if at line 5.
        """
        care_of_text = f"c/o {care_of}"

        # If we're at line 5, overwrite line 4 instead
        line = 4 if start_line == 5 else start_line

        for i in range(0, len(care_of_text), 35):
            if line >= 5:
                break

            care_of_line = normalize_short_lines(care_of_text[i : i + 35])
            setattr(self, f"priority_name{line}", care_of_line)
            setattr(self, f"info_name{line}", care_of_line)
            line += 1

    def _set_address_fields(self, contact: Contact):
        """Set priority and info address fields."""
        address = contact.address[:35] if contact.address else ""

        self.priority_address1 = address
        self.priority_city = contact.city
        self.priority_postalcode = contact.postal_code

        self.info_address1 = address
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
    # Only one of the following can be set: 'order_item_number' or 'wbs_element'
    order_item_number = Field(
        name="OrderItemNumber", validators=[MaxLengthValidator(12)]
    )
    wbs_element = Field(
        name="WBS_Element", validators=None
    )  # Used for "SAP project number"
    functional_area = Field(name="FunctionalArea", validators=[MaxLengthValidator(6)])
    business_entity = Field(name="BusinessEntity", validators=[MaxLengthValidator(8)])
    building = Field(name="Building", validators=[MaxLengthValidator(8)])
    rental_object = Field(name="RentalObject", validators=[MaxLengthValidator(8)])

    class Meta:
        element_name = "LineItem"

    def validate(self):
        super().validate()

        # Only one of 'order_item_number' or 'wbs_element' can be set.
        if self.order_item_number is not None and self.wbs_element is not None:
            raise ValidationError(
                "Only one of 'order_item_number' or 'wbs_element' can be set."
            )


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
        name="PaymentReference",
        validators=[MaxLengthValidator(30), validate_payment_reference],
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
