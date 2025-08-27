"""
Import lease rights transfers from National Land Survey of Finland (Maanmittauslaitos)
"""

import io
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...enums import LeaseholdTransferPartyType
from ...models import (
    LeaseholdTransfer,
    LeaseholdTransferImportLog,
    LeaseholdTransferParty,
    LeaseholdTransferProperty,
)

NS = {  # Namespace links for NLS XMLs
    "y": "http://xml.nls.fi/ktjkir/yhteinen/2018/02/01",
    "eavo": "http://xml.nls.fi/ktjkir/eraajo/vuokraoikeustiedot/2018/02/01",
    "trpt": "http://xml.nls.fi/ktjkir/perustiedot/2018/02/01",
    "trvo": "http://xml.nls.fi/ktjkir/vuokraoikeustiedot/2018/02/01",
}


def get_import_dir() -> str:
    return settings.NLS_IMPORT_ROOT


def get_name_from_xml_elem(elem: ElementTree.Element[str]) -> str | None:
    name = ""

    first_names_xml = elem.find(".//y:etunimet", NS)
    if first_names_xml is not None:
        name += first_names_xml.text
    last_name_xml = elem.find(".//y:sukunimi", NS)
    if last_name_xml is not None:
        name += " " + last_name_xml.text if name else last_name_xml.text

    if not name:
        name_xml = elem.find(".//y:nimi", NS)
        if name_xml is not None:
            name = name_xml.text

    return name


def get_business_id_or_none_from_xml_elem(elem: ElementTree.Element[str]) -> str | None:
    business_id = None

    business_id_xml = elem.find(".//y:ytunnus", NS)
    if business_id_xml is not None:
        business_id = business_id_xml.text
    return business_id


def get_national_id_or_none_from_xml_elem(elem: ElementTree.Element[str]) -> str | None:
    national_id = None

    national_id_xml = elem.find(".//y:henkilotunnus", NS)
    if national_id_xml is not None:
        national_id = national_id_xml.text
    return national_id


class Command(BaseCommand):
    help = __doc__.strip()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nls_url: str = settings.NLS_HELSINKI_FOLDER_URL
        self.nls_user: str = settings.NLS_HELSINKI_USERNAME
        self.nls_password: str = settings.NLS_HELSINKI_PASSWORD.encode("utf-8")
        self.touched_transfers_count = 0

    def _auth_get(self, url) -> requests.Response:
        return requests.get(url, auth=(self.nls_user, self.nls_password))

    def _check_import_directory(self) -> None:
        if not os.path.isdir(get_import_dir()):
            self.stdout.write(
                f'Directory "{get_import_dir()}" does not exist. Please create it.'
            )
            sys.exit(-1)

        try:
            fp = tempfile.TemporaryFile(dir=get_import_dir())
            fp.close()
        except PermissionError:
            self.stdout.write(f'Can not create file in directory "{get_import_dir()}".')
            sys.exit(-1)

    def handle(self, *args, **options) -> None:
        self._check_import_directory()

        target_folder_path = self.nls_url + "ktjkiraineistoluovutus/"

        folder_response = self._auth_get(target_folder_path)

        if folder_response.status_code != 200:
            raise CommandError("Failed to connect to NLS server")

        html_soup = BeautifulSoup(folder_response.content, "html.parser")

        imported_archives = 0
        new_archives = 0

        for link in html_soup.select("a[href*=vuokraoikeudet_muuttuneet]"):
            file_link = link["href"]
            file_name = file_link.split("/")[-1]

            if LeaseholdTransferImportLog.objects.filter(file_name=file_name).exists():
                # skipping this already processed archive
                continue

            zip_file_response = self._auth_get(target_folder_path + file_name)
            zip_bytes = zip_file_response.content

            with open(os.path.join(get_import_dir(), file_name), "wb") as local_zip:
                local_zip.write(zip_bytes)
                local_zip.close()

            archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
            xml_file = archive.read("vuokraoikeustiedot.xml")
            self._handle_xml_file(xml_file)

            (
                processed_archive_object,
                created,
            ) = LeaseholdTransferImportLog.objects.get_or_create(file_name=file_name)

            # save to update the timestamp, if object existed
            processed_archive_object.save()

            imported_archives += 1
            if created:
                new_archives += 1

        self.stdout.write(f"Imported data from {imported_archives} archive(s)")
        self.stdout.write(f"From which {new_archives} were new")
        self.stdout.write(f"Touched {self.touched_transfers_count} transfer(s)")

    def _handle_xml_file(self, xml_file: bytes) -> None:
        root = ElementTree.fromstring(xml_file)

        for entry in root.findall("./eavo:Laitos", NS):
            leasehold_items = entry.findall(".//trvo:ErityinenOikeusAsia", NS)

            if not leasehold_items:
                # go to next laitos
                continue

            for item in leasehold_items:
                item_type = item.find("./y:asianLaatu", NS).text

                if item_type != "EO03":
                    # only EO03 == OikeuksienSiirto
                    # go to next item
                    continue

                item_status = item.find("./y:asianTila", NS).text

                if item_status != "03":
                    # only 03 == loppuun saatettu
                    # go to next item
                    continue

                decision = item.find("./y:Ratkaisu", NS)
                transfer_shares = item.find("./trvo:osuudetAsianKohteesta", NS)

                if decision is None or transfer_shares is None:
                    # probably an update to previous transfer
                    # go to next item
                    continue

                decision_date_el = decision.find("./y:ratkaisupvm", NS)
                decision_date = None
                if decision_date_el is not None:
                    decision_date_str = decision_date_el.text  # e.g. '2016-05-15'
                    decision_date = datetime.strptime(
                        decision_date_str, "%Y-%d-%M"
                    ).replace(tzinfo=ZoneInfo("Europe/Helsinki"))

                institution_identifier = entry.find(".//y:laitostunnus", NS).text

                # check if at least 1 leasehold transfer already exists
                transfer = LeaseholdTransfer.all_objects.filter(
                    institution_identifier=institution_identifier,
                    decision_date=decision_date,
                ).last()

                if transfer is None:
                    transfer = LeaseholdTransfer.objects.create(
                        institution_identifier=institution_identifier,
                        decision_date=decision_date,
                    )

                self._handle_lease_properties(transfer, entry)

                self._handle_lease_parties(transfer, entry, transfer_shares)

                self.touched_transfers_count += 1

    @staticmethod
    def _handle_lease_properties(
        transfer: LeaseholdTransfer, entry_xml: ElementTree.Element[str]
    ) -> None:
        properties_xml_elems = entry_xml.findall(
            "./trpt:laitoksenPerustiedot//trpt:EOKohde", NS
        )

        for prop_element in properties_xml_elems:
            property_id = prop_element.find("./y:kiinteistotunnus", NS)
            if property_id is not None:
                prop, _ = LeaseholdTransferProperty.objects.get_or_create(
                    identifier=property_id.text, transfer=transfer
                )

    @staticmethod
    def _handle_lease_parties(
        transfer: LeaseholdTransfer,
        entry_xml: ElementTree.Element[str],
        transfer_shares_xml: ElementTree.Element[str],
    ) -> None:
        lessors_xml_elems = entry_xml.findall(
            "./trpt:laitoksenPerustiedot/trpt:eoHenkilot/y:Henkilo", NS
        )

        for lessor_element in lessors_xml_elems:
            lessor_name = get_name_from_xml_elem(lessor_element)
            business_id = get_business_id_or_none_from_xml_elem(lessor_element)
            national_id = get_national_id_or_none_from_xml_elem(lessor_element)
            if lessor_name is not None:
                lessor, _ = LeaseholdTransferParty.objects.get_or_create(
                    type=LeaseholdTransferPartyType.LESSOR,
                    name=lessor_name,
                    business_id=business_id,
                    national_identification_number=national_id,
                    transfer=transfer,
                )

        for share_elem in transfer_shares_xml.findall("./trvo:OsuusAsianKohteesta", NS):
            share_numerator = int(share_elem.find("./y:osoittaja", NS).text)
            share_denominator = int(share_elem.find("./y:nimittaja", NS).text)

            for conveyor_xml_elem in share_elem.findall(
                ".//y:saannonHenkilot/y:Henkilo", NS
            ):
                conveyor_name = get_name_from_xml_elem(conveyor_xml_elem)
                business_id = get_business_id_or_none_from_xml_elem(conveyor_xml_elem)
                national_id = get_national_id_or_none_from_xml_elem(conveyor_xml_elem)
                conveyor, _ = LeaseholdTransferParty.objects.get_or_create(
                    type=LeaseholdTransferPartyType.CONVEYOR,
                    name=conveyor_name,
                    business_id=business_id,
                    national_identification_number=national_id,
                    transfer=transfer,
                )

            for acquirer_xml_elem in share_elem.findall(
                "./y:osuudenHenkilot/y:Henkilo", NS
            ):
                acquirer_name = get_name_from_xml_elem(acquirer_xml_elem)
                business_id = get_business_id_or_none_from_xml_elem(acquirer_xml_elem)
                national_id = get_national_id_or_none_from_xml_elem(acquirer_xml_elem)
                acquirer, _ = LeaseholdTransferParty.objects.get_or_create(
                    type=LeaseholdTransferPartyType.ACQUIRER,
                    name=acquirer_name,
                    share_numerator=share_numerator,
                    share_denominator=share_denominator,
                    business_id=business_id,
                    national_identification_number=national_id,
                    transfer=transfer,
                )
