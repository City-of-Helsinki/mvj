from django.core.management.base import BaseCommand, CommandError

from leasing.enums import ContactType, SapSalesOfficeNumber, ServiceUnitId
from leasing.models import Contact, ServiceUnit

SERVICE_UNITS = [
    {
        "id": ServiceUnitId.MAKE.value,
        "contact_name": "KYMP/MAKE ja Tontit",
        "sap_sales_office": SapSalesOfficeNumber.MAKE.value,
        "email": "MAKE@example.com",
    },
    {
        "id": ServiceUnitId.AKV.value,
        "contact_name": "KYMP/Alueiden käyttö ja valvonta",
        "sap_sales_office": SapSalesOfficeNumber.AKV.value,
        "email": "AKV@example.com",
    },
    {
        "id": ServiceUnitId.KUVA_LIPA.value,
        "contact_name": "KUVA/Liikuntapaikkapalvelut",
        "sap_sales_office": SapSalesOfficeNumber.KUVA.value,
        "email": "KUVA@example.com",
    },
    {
        "id": ServiceUnitId.KUVA_UPA.value,
        "contact_name": "KUVA/Ulkoilupalvelut",
        "sap_sales_office": SapSalesOfficeNumber.KUVA.value,
        "email": "KUVA@example.com",
    },
    {
        "id": ServiceUnitId.KUVA_NUP.value,
        "contact_name": "KUVA/Nuorisopalvelut",
        "sap_sales_office": SapSalesOfficeNumber.KUVA.value,
        "email": "KUVA@example.com",
    },
]


class Command(BaseCommand):
    help = "Adds the default lessor contacts for all the Service units"

    def handle(self, *args, **options):
        service_units = {su.id: su for su in ServiceUnit.objects.all()}
        for service_unit_data in SERVICE_UNITS:
            if service_unit_data["id"] not in service_units.keys():
                raise CommandError(
                    "Service unit id {} missing. Please load service_unit.json fixture first.".format(
                        service_unit_data["id"]
                    )
                )

        self.stdout.write("Creating lessor contacts for Service units...")
        for service_unit_data in SERVICE_UNITS:
            self.stdout.write(
                " Service unit: {}".format(service_units[service_unit_data["id"]].name)
            )
            self.stdout.write(
                " Contact name: {}".format(service_unit_data["contact_name"])
            )
            (contact, contact_created) = Contact.objects.get_or_create(
                service_unit=service_units[service_unit_data["id"]],
                is_lessor=True,
                name=service_unit_data["contact_name"],
                sap_sales_office=service_unit_data["sap_sales_office"],
                email=service_unit_data["email"],
                defaults={
                    "type": ContactType.UNIT,
                    "address": "PL2214",
                    "postal_code": "00099",
                    "city": "Helsingin kaupunki",
                    "business_id": "",
                },
            )
            self.stdout.write(
                " Created.\n" if contact_created else " Already exists.\n"
            )
