import requests
from django.core.management.base import BaseCommand, CommandError

from leasing.models import Index


class Command(BaseCommand):
    help = 'Import index from stat.fi'

    def handle(self, *args, **options):
        r = requests.post('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin/hin/khi/statfin_khi_pxt_008.px',
                          data='{"query":[],"response":{"format":"json"}}')

        if r.status_code != 200:
            raise CommandError('Failed to download index')

        data = r.json().get("data")

        for row in data:
            (year, month, _) = row["key"]

            year = int(year)

            if month == 'M01-M12':
                month = None
            else:
                month = int(month.lstrip('M0'))

            number = row["values"][0]

            if number == '.':
                continue

            Index.objects.update_or_create(year=year, month=month, defaults={
                'number': number,
            })

            self.stdout.write('{}:{} = {}'.format(year, month, number))
