from django.core.management.base import BaseCommand

from leasing.models import ReceivableType, ServiceUnit

RECEIVABLE_TYPE_RENT_NAME = "Maanvuokraus"
RECEIVABLE_TYPE_COLLATERAL_NAME = "Rahavakuus"


class Command(BaseCommand):
    help = "Adds the default receivable types for all the Service units"

    def handle(self, *args, **options):
        self.stdout.write("Creating receivable types for Service units...")
        for service_unit in ServiceUnit.objects.all():
            self.stdout.write("\n Service unit: {}".format(service_unit.name))

            self.stdout.write(" Receivable type rent...", ending="")
            (
                receivable_type,
                receivable_type_created,
            ) = ReceivableType.objects.get_or_create(
                service_unit=service_unit,
                name=RECEIVABLE_TYPE_RENT_NAME,
            )
            self.stdout.write(
                " Created.\n" if receivable_type_created else " Already exists.\n"
            )
            service_unit.default_receivable_type_rent = receivable_type

            self.stdout.write(" Receivable type collateral...", ending="")
            (
                receivable_type,
                receivable_type_created,
            ) = ReceivableType.objects.get_or_create(
                service_unit=service_unit,
                name=RECEIVABLE_TYPE_COLLATERAL_NAME,
            )
            self.stdout.write(
                "Created.\n" if receivable_type_created else "Already exists.\n"
            )
            service_unit.default_receivable_type_collateral = receivable_type
            service_unit.save()
