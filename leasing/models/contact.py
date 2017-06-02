from xml.etree import ElementTree

from django.db import models
from django.utils.translation import ugettext_lazy as _

from leasing.models.mixins import TimestampedModelMixin


class Contact(TimestampedModelMixin):
    name = models.CharField(verbose_name=_("Name"), null=True, blank=True, max_length=255)
    address = models.CharField(verbose_name=_("Address"), null=True, blank=True, max_length=2048)
    billing_address = models.CharField(verbose_name=_("Billing address"), null=True, blank=True,
                                       max_length=2048)
    electronic_billing_details = models.CharField(verbose_name=_("Electronic billing details"), null=True, blank=True,
                                                  max_length=2048)
    email = models.EmailField(verbose_name=_("Email address"), null=True, blank=True)
    phone = models.CharField(verbose_name=_("Phone number"), null=True, blank=True, max_length=255)

    organization_name = models.CharField(verbose_name=_("Organization name"), null=True, blank=True, max_length=255)
    organization_address = models.CharField(verbose_name=_("Organization address"), null=True, blank=True,
                                            max_length=255)
    organization_is_company = models.BooleanField(verbose_name=_("Is organization a company"), default=False)
    organization_id = models.CharField(verbose_name=_("Organization id"), null=True, blank=True, max_length=255)
    organization_revenue = models.CharField(verbose_name=_("Organization revenue"), null=True, blank=True,
                                            max_length=255)

    def __str__(self):
        parts = []

        if self.name:
            parts.append(self.name)

        if self.organization_name:
            parts.append(self.organization_name)

        return ' '.join(parts)

    def as_laske_xml(self, tag_name):
        root = ElementTree.Element(tag_name)
        ElementTree.SubElement(root, 'SAPCustomerID')
        ElementTree.SubElement(root, 'CustomerID')
        customer_yid = ElementTree.SubElement(root, 'CustomerYID')
        customer_yid.text = self.organization_id if self.organization_id else None
        ElementTree.SubElement(root, 'CustomerOVT')
        ElementTree.SubElement(root, 'TemporaryAddress1')
        ElementTree.SubElement(root, 'TemporaryAddress2')
        ElementTree.SubElement(root, 'TemporaryPOCode')
        ElementTree.SubElement(root, 'TemporaryPOCity')
        ElementTree.SubElement(root, 'TemporaryPOPostalcode')
        ElementTree.SubElement(root, 'TemporaryCity')
        ElementTree.SubElement(root, 'TemporaryPostalcode')
        priority_name1 = ElementTree.SubElement(root, 'PriorityName1')
        if self.organization_name:
            priority_name1.text = self.organization_name
        elif self.name:
            priority_name1.text = self.name
        ElementTree.SubElement(root, 'PriorityName2')
        ElementTree.SubElement(root, 'PriorityName3')
        ElementTree.SubElement(root, 'PriorityName4')
        priority_address1 = ElementTree.SubElement(root, 'PriorityAddress1')
        if self.organization_address:
            priority_address1.text = self.organization_address
        elif self.address:
            priority_address1.text = self.address
        ElementTree.SubElement(root, 'PriorityAddress2')
        ElementTree.SubElement(root, 'PriorityPOCode')
        ElementTree.SubElement(root, 'PriorityPOCity')
        ElementTree.SubElement(root, 'PriorityPOPostalcode')
        ElementTree.SubElement(root, 'PriorityCity')
        ElementTree.SubElement(root, 'PriorityPostalcode')
        ElementTree.SubElement(root, 'InfoCustomerID')
        info_customer_yid = ElementTree.SubElement(root, 'InfoCustomerYID')
        info_customer_yid.text = self.organization_id if self.organization_id else None
        ElementTree.SubElement(root, 'InfoCustomerOVT')
        info_name1 = ElementTree.SubElement(root, 'InfoName1')
        if self.organization_name:
            info_name1.text = self.organization_name
        elif self.name:
            info_name1.text = self.name
        ElementTree.SubElement(root, 'InfoName2')
        ElementTree.SubElement(root, 'InfoName3')
        ElementTree.SubElement(root, 'InfoName4')
        info_address1 = ElementTree.SubElement(root, 'InfoAddress1')
        if self.organization_address:
            info_address1.text = self.organization_address
        elif self.address:
            info_address1.text = self.address
        ElementTree.SubElement(root, 'InfoAddress2')
        ElementTree.SubElement(root, 'InfoPOCode')
        ElementTree.SubElement(root, 'InfoPOCity')
        ElementTree.SubElement(root, 'InfoPOPostalcode')
        ElementTree.SubElement(root, 'InfoCity')
        ElementTree.SubElement(root, 'InfoPostalcode')

        return root
