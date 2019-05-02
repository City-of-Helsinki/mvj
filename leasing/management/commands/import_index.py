import requests
from django.core.management.base import BaseCommand, CommandError

from leasing.models import Index
from leasing.models.rent import LegacyIndex


def get_values_from_row(row):
    (year, month, _) = row["key"]

    year = int(year)

    if month == 'M01-M12':
        month = None
    else:
        month = int(month.lstrip('M0'))

    number = row["values"][0]

    if number == '.':
        number = None
    else:
        number = int(number)

    return year, month, number


def get_data(url):
    query_string = '{"query":[],"response":{"format":"json"}}'

    r = requests.post(url, data=query_string)

    if r.status_code != 200:
        raise CommandError('Failed to download index')

    return r.json().get("data")


class Command(BaseCommand):
    help = 'Import index from stat.fi'

    def handle(self, *args, **options):  # NOQA
        data = get_data('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin/hin/khi/statfin_khi_pxt_008.px')

        for row in data:
            (year, month, number) = get_values_from_row(row)

            if number is None:
                continue

            Index.objects.update_or_create(year=year, month=month, defaults={
                'number': number,
            })

            self.stdout.write('{}:{} = {}'.format(year, month, number))

        data = get_data('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin/hin/khi/statfin_khi_pxt_009.px')

        for row in data:
            (year, month, number) = get_values_from_row(row)

            if number is None:
                continue

            try:
                index = Index.objects.get(year=year, month=month)
            except Index.DoesNotExist:
                index = Index.objects.create(year=year, month=month, number=0)

            LegacyIndex.objects.update_or_create(index=index, defaults={
                'number_1938': number,
            })

        data = get_data('http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin/hin/khi/statfin_khi_pxt_015.px')

        for row in data:
            (year, month, number) = get_values_from_row(row)

            if number is None:
                continue

            try:
                index = Index.objects.get(year=year, month=month)
            except Index.DoesNotExist:
                index = Index.objects.create(year=year, month=month, number=0)

            LegacyIndex.objects.update_or_create(index=index, defaults={
                'number_1914': number,
            })
