import argparse

from django.core.management.base import BaseCommand

from leasing.models import Contact


def read_post_codes(file):
    code_to_city_name = {}

    for row in file:
        code = row[13:18]
        # city_name = row[18:48].strip().capitalize()
        city_name = row[18:48].strip()

        code_to_city_name[code] = city_name

    return code_to_city_name


class Command(BaseCommand):
    help = "Sets contact city from the postcode"

    def add_arguments(self, parser):
        parser.add_argument(
            "pcf_file",
            type=argparse.FileType("r", encoding="iso8859-1"),
            help="File with all the Finnish post codes. Can be obtained from "
            "https://support.posti.fi/fi/postinumeropalvelut/postinumerotiedostot.html",
        )

    def handle(self, *args, **options):
        code_to_city_name = read_post_codes(options["pcf_file"])

        from auditlog.registry import auditlog

        # Unregister Contact model from auditlog
        auditlog.unregister(Contact)

        contacts = Contact.objects.filter(city__isnull=True)
        self.stdout.write("{} contacts without city".format(contacts.count()))

        for contact in contacts:
            if not contact.postal_code:
                self.stdout.write(
                    "Contact id {} has no postal code. Skipping.".format(contact.id)
                )
                continue

            if contact.postal_code not in code_to_city_name.keys():
                self.stdout.write(
                    'Contact id {} has an unknown postal code "{}". Skipping.'.format(
                        contact.id, contact.postal_code
                    )
                )
                continue

            contact.city = code_to_city_name[contact.postal_code]
            contact.save()
