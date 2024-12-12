import os
import tempfile

import pytest

from leasing.management.commands.load_csv_leasearea import Command
from leasing.models.land_area import LeaseArea


@pytest.mark.django_db
def test_load_leasearea(lease_factory):
    lease = lease_factory()
    csv_content = "\n".join(
        [
            "mvj_vuokraustunnus,mvj_kohteen_tunnus,mvj_maaritelma,mvj_pinta_ala,mvj_sijainti,mvj_osoite,mvj_postinumero,mvj_kaupunki,mvj_ensisijainen_osoite",  # noqa: E501
            f"{lease.identifier.identifier},456,Kaavayksikkö,1000,Yläpuolella,Address1,12345,City1,Kyllä",
            f"{lease.identifier.identifier},789,Määräala,2000,Alapuolella,Address2,02345,City2,Kyllä",
        ]
    )
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(csv_content)
        csv_file = f.name
    try:
        command = Command()
        command.handle(csv=csv_file)

        lease_area1 = LeaseArea.objects.get(
            lease_id=lease.id, addresses__address="Address1"
        )
        lease_area2 = LeaseArea.objects.get(
            lease_id=lease.id, addresses__address="Address2"
        )
        assert lease_area1.area == 1000
        assert lease_area2.area == 2000
        assert lease.lease_areas.count() == 2
    finally:
        os.remove(csv_file)


def test_check_headers():
    command = Command()
    with pytest.raises(ValueError) as exc:
        command.check_headers(
            ["mvj_vuokraustunnus", "mvj_kohteen_tunnus", "mvj_maaritelma"],
            [
                "mvj_vuokraustunnus",
                "mvj_kohteen_tunnus",
                "mvj_maaritelma",
                "missing_header",
            ],
        )
    assert exc.value.args[0] == "Missing headers: missing_header"
    with pytest.raises(ValueError) as exc:
        command.check_headers(
            [
                "mvj_vuokraustunnus",
                "mvj_kohteen_tunnus",
                "mvj_maaritelma",
                "extra_header",
            ],
            [
                "mvj_vuokraustunnus",
                "mvj_kohteen_tunnus",
                "mvj_maaritelma",
            ],
        )
    assert exc.value.args[0] == "Extra headers: extra_header"

    command.check_headers(
        ["mvj_vuokraustunnus", "mvj_kohteen_tunnus", "mvj_maaritelma"],
        ["mvj_vuokraustunnus", "mvj_kohteen_tunnus", "mvj_maaritelma"],
    )


def test_transform_is_primary():
    command = Command()
    assert command._transform_is_primary("Kyllä") is True
    assert command._transform_is_primary("Ei") is False
    assert command._transform_is_primary(None) is False


@pytest.mark.django_db
def test_pre_validate_csv(lease_factory):
    lease = lease_factory()
    incorrect_type = "incorrect_type"
    incorrect_location = "incorrect_location"
    csv_content = "\n".join(
        [
            "mvj_vuokraustunnus,mvj_kohteen_tunnus,mvj_maaritelma,mvj_pinta_ala,mvj_sijainti,mvj_osoite,mvj_postinumero,mvj_kaupunki,mvj_ensisijainen_osoite",  # noqa: E501
            f"{lease.identifier.identifier},456,{incorrect_type},1000,Yläpuolella,Address1,12345,City1,Kyllä",
            f"{lease.identifier.identifier},789,Määräala,2000,{incorrect_location},Address2,02345,City2,Kyllä",
        ]
    )
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(csv_content)
        csv_file = f.name
    try:
        command = Command()
        with pytest.raises(ValueError) as exc:
            command.handle(csv=csv_file)
        assert exc.value.args[0] == "Invalid data in CSV file"

    finally:
        os.remove(csv_file)
