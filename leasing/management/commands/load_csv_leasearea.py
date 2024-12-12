import csv
from collections import OrderedDict

from django.core.management.base import BaseCommand
from django.db import transaction

from leasing.enums import LeaseAreaType, LocationType
from leasing.models.land_area import LeaseArea, LeaseAreaAddress
from leasing.models.lease import Lease


class Command(BaseCommand):
    # Usage: `python manage.py load_csv_leasearea --csv path/to/file.csv`
    help = "Load data from a CSV file to LeaseArea model and LeaseAreaAddress model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv", type=str, required=False, help="The path to the CSV file"
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs.get("csv")
        if not csv_file:
            # Print the expected headers if argument `--csv` is not provided
            self.stdout.write(",".join(self._get_expected_headers()))
            return

        self.pre_validate_csv_rows(csv_file)

        with open(csv_file) as file:
            reader = csv.DictReader(
                file,
                delimiter=",",
            )

            try:
                with transaction.atomic():
                    for row in reader:
                        self.create_leasearea(row)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERROR: Data loading failed: {e}"))

        self.stdout.write(self.style.SUCCESS("Data loaded successfully"))

    def _get_fieldnames_mappings(self):
        fieldnames_mapping_lease = OrderedDict(
            [
                ("mvj_vuokraustunnus", "lease_identifier"),
            ]
        )
        fieldnames_mapping_leasearea = OrderedDict(
            [
                ("mvj_kohteen_tunnus", "identifier"),
                ("mvj_maaritelma", "type"),
                ("mvj_pinta_ala", "area"),
                ("mvj_sijainti", "location"),
            ]
        )
        fieldnames_mapping_leasearea_address = OrderedDict(
            [
                ("mvj_osoite", "address"),
                ("mvj_postinumero", "postal_code"),
                ("mvj_kaupunki", "city"),
                ("mvj_ensisijainen_osoite", "is_primary"),
            ]
        )

        return (
            fieldnames_mapping_lease,
            fieldnames_mapping_leasearea,
            fieldnames_mapping_leasearea_address,
        )

    def _transform_keys(self, row: dict, fieldnames_mapping: OrderedDict):
        """Transform the keys in fieldnames_mapping from csv headers to model field names."""
        return {
            fieldnames_mapping[key]: value
            for key, value in row.items()
            if key in fieldnames_mapping
        }

    def _transform_is_primary(self, value):
        """Expected values are 'Kyllä' or 'Ei', but if it is not correctly set we can't assume it is primary.
        Sets the value to False unless it is 'Kyllä'."""
        return value == "Kyllä"

    def _get_expected_headers(self):
        (
            fieldnames_mapping_lease,
            fieldnames_mapping_leasearea,
            fieldnames_mapping_leasearea_address,
        ) = self._get_fieldnames_mappings()

        return list(
            list(fieldnames_mapping_lease.keys())
            + list(fieldnames_mapping_leasearea.keys())
            + list(fieldnames_mapping_leasearea_address.keys())
        )

    def check_headers(self, actual_headers, expected_headers=None):
        if expected_headers is None:
            expected_headers = self._get_expected_headers()

        missing_headers = [
            header for header in expected_headers if header not in actual_headers
        ]
        if missing_headers:
            raise ValueError(f"Missing headers: {', '.join(missing_headers)}")

        extra_headers = [
            header for header in actual_headers if header not in expected_headers
        ]
        if extra_headers:
            raise ValueError(f"Extra headers: {', '.join(extra_headers)}")

    def create_leasearea(self, row):
        (
            fieldnames_mapping_lease,
            fieldnames_mapping_leasearea,
            fieldnames_mapping_leasearea_address,
        ) = self._get_fieldnames_mappings()

        # Transform the row to match the Lease model fields
        lease_data = self._transform_keys(row, fieldnames_mapping_lease)
        lease_identifier = lease_data.get("lease_identifier")

        lease = Lease.objects.get(identifier__identifier=lease_identifier)

        # Transform the row to match the LeaseArea model fields
        leasearea_data = self._transform_keys(row, fieldnames_mapping_leasearea)
        leasearea_data["lease_id"] = lease.id

        # Create the LeaseArea object
        lease_area = LeaseArea.objects.create(**leasearea_data)

        # Transform the row to match the LeaseAreaAddress model fields
        leasearea_address_data = self._transform_keys(
            row, fieldnames_mapping_leasearea_address
        )
        leasearea_address_data["lease_area_id"] = lease_area.id
        leasearea_address_data["is_primary"] = self._transform_is_primary(
            leasearea_address_data.get("is_primary")
        )

        # Create the LeaseAreaAddress object
        lease_area_address = LeaseAreaAddress.objects.create(**leasearea_address_data)
        self.stdout.write(
            self.style.SUCCESS(
                f"Created LeaseArea.id: {lease_area.id}, LeaseAreaAddress.id: {lease_area_address.id}"
            )
        )

    def pre_validate_csv_rows(self, csv_file):
        """Prevalidate some strict rules before processing the CSV file.
        Attempts to identify multiple issues at once instead of one by one."""
        with open(csv_file) as file:
            reader = csv.DictReader(
                file,
                delimiter=",",
            )

            self.check_headers(reader.fieldnames)
            errors = []
            warnings = []
            for i, row in enumerate(reader, start=2):
                # Errors
                if row.get("mvj_maaritelma") not in [x.value for x in LeaseAreaType]:
                    errors.append(
                        f"Row {i}: Invalid mvj_maaritelma value: {row.get('mvj_maaritelma')}"
                    )
                if row.get("mvj_sijainti") not in [x.value for x in LocationType]:
                    errors.append(
                        f"Row {i}: Invalid mvj_sijainti value: {row.get('mvj_sijainti')}"
                    )

                # Warnings
                ensisijainen_osoite = row.get("mvj_ensisijainen_osoite")
                if ensisijainen_osoite not in ["Kyllä", "Ei"]:
                    warnings.append(
                        f"Row {i}: Invalid mvj_ensisijainen_osoite value: {ensisijainen_osoite} transformed to: {self._transform_is_primary(ensisijainen_osoite)}"  # noqa: E501
                    )

            if errors:
                self.stdout.write(self.style.ERROR("\n".join(errors)))
                raise ValueError("Invalid data in CSV file")

            if warnings:
                self.stdout.write(self.style.WARNING("\n".join(warnings)))
