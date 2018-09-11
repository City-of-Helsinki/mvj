import datetime
import re
from decimal import Decimal
from xml.etree import ElementTree

import requests
from django.core.management.base import BaseCommand, CommandError

from leasing.models.debt_collection import InterestRate


class Command(BaseCommand):
    help = 'Import interest rate from suomenpankki.fi'

    def handle(self, *args, **options):
        r = requests.get('https://www.suomenpankki.fi/WebForms/ReportViewerPage.aspx',
                         params={
                             'report': '/tilastot/markkina-_ja_hallinnolliset_korot/viitekorko_fi',
                             'output': 'xml',
                         })

        if r.status_code != 200:
            raise CommandError('Failed to download interest rates')

        root = ElementTree.fromstring(r.content)

        for year_element in root.findall('.//{viitekorko_fi}matrix1_year'):
            current_year = int(year_element.attrib.get('txtb_year'))

            for period_element in year_element.findall('.//{viitekorko_fi}matrix1_Period'):
                current_period_string = period_element.attrib.get('Period')
                period_match = re.match(
                    r'(?P<start_day>\d+)\.(?P<start_month>\d+)\..(?P<end_day>\d+)\.(?P<end_month>\d+)',
                    current_period_string)

                if not period_match:
                    continue

                start_date = datetime.date(year=current_year, month=int(period_match.group('start_month')), day=int(
                    period_match.group('start_day')))
                end_date = datetime.date(year=current_year, month=int(period_match.group('end_month')), day=int(
                    period_match.group('end_day')))

                currency_elements = period_element.findall(
                    './{viitekorko_fi}col_grp_currency_Collection/{viitekorko_fi}col_grp_currency')

                rates = {}
                for currency_element in currency_elements:
                    interest_type_string = currency_element.attrib.get('txtb_currency')
                    if interest_type_string not in [
                            'Korkolain perusteella vahvistettu viitekorko',
                            'Viivästyskorko, kun velasta ei ole sovittu maksettavaksi korkoa']:
                        continue

                    cell = currency_element.find('./{viitekorko_fi}Cell')
                    interest_value_string = cell.attrib.get('txtb_value', '')
                    if not interest_value_string:
                        continue

                    interest_value = Decimal(cell.attrib.get('txtb_value', ''))

                    rates[interest_type_string] = interest_value

                    self.stdout.write('{} - {} {}: {}'.format(start_date, end_date, interest_type_string,
                                                              interest_value))

                InterestRate.objects.update_or_create(
                    start_date=start_date, end_date=end_date,
                    reference_rate=rates['Korkolain perusteella vahvistettu viitekorko'],
                    penalty_rate=rates['Viivästyskorko, kun velasta ei ole sovittu maksettavaksi korkoa'])
