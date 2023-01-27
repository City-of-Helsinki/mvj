import re

import requests
from django.core.management.base import BaseCommand, CommandError

from leasing.models import Index
from leasing.models.rent import LegacyIndex

INDEX_IMPORTS = [
    {
        "name": "Elinkustannusindeksi 1951:100 (kuukasittaiset)",
        "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/statfin_khi_pxt_11xl.px",
    },
    {
        "name": "Elinkustannusindeksi 1951:100 (vuosittaiset)",
        "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/statfin_khi_pxt_11xm.px",
    },
    {
        "name": "Elinkustannusindeksi 1938:8-1939:7 = 100 (kuukausittaiset)",
        "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/statfin_khi_pxt_11xn.px",
        "legacy": "number_1938",
    },
    {
        "name": "Elinkustannusindeksi 1938:8-1939:7 = 100 (vuosittaiset)",
        "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/statfin_khi_pxt_11xp.px",
        "legacy": "number_1938",
    },
    {
        "name": "Elinkustannusindeksi 1914:1-6 = 100 (vuosittaiset)",
        "url": "https://statfin.stat.fi/PXWeb/api/v1/fi/StatFin/statfin_khi_pxt_11xy.px",
        "legacy": "number_1914",
    },
]


def get_values_from_row(row):
    matches = re.match(r"(?P<year>\d+)(?:M(?P<month>\d+))?", row["key"][0])

    year = int(matches.group("year"))

    month = None
    if matches.group("month"):
        month = int(matches.group("month"))

    number = row["values"][0]

    if number == ".":
        number = None
    else:
        number = int(number)

    return year, month, number


def get_data(url):
    query_string = '{"query":[],"response":{"format":"json"}}'

    r = requests.post(url, data=query_string)

    if r.status_code != 200:
        raise CommandError("Failed to download index")

    return r.json().get("data")


class Command(BaseCommand):
    help = "Import index from stat.fi"

    def handle(self, *args, **options):
        for index_import in INDEX_IMPORTS:
            self.stdout.write(index_import["name"])

            data = get_data(index_import["url"])

            for row in data:
                (year, month, number) = get_values_from_row(row)

                if number is None:
                    continue

                if "legacy" not in index_import:
                    Index.objects.update_or_create(
                        year=year, month=month, defaults={"number": number}
                    )

                else:
                    try:
                        index = Index.objects.get(year=year, month=month)
                    except Index.DoesNotExist:
                        # No index for this month/year, add a dummy entry
                        index = Index.objects.create(year=year, month=month, number=0)

                    LegacyIndex.objects.update_or_create(
                        index=index, defaults={index_import["legacy"]: number}
                    )

                self.stdout.write(" {}:{} = {}".format(year, month, number))
