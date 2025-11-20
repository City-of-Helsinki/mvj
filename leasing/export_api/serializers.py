import json

from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from django.utils.translation import override
from rest_framework import serializers

from leasing.models.contact import Contact
from leasing.models.land_area import LeaseArea
from leasing.models.lease import Lease
from leasing.models.map_layers import VipunenMapLayer
from users.models import User


class ExportLeaseAreaSerializer(serializers.ModelSerializer):
    vuokraus_id = serializers.IntegerField(source="lease.id")
    kiinteistotunnus = serializers.CharField(source="identifier")
    tyypin_tunnus = serializers.CharField(source="lease.type.identifier")
    vuokraustunnus = serializers.CharField(source="lease.identifier.identifier")
    sopimusnumero = serializers.CharField(source="latest_contract_number")
    sopimus_allekirjoitettu = serializers.DateField(source="latest_signing_date")
    vuokraus_diaari = serializers.CharField(source="lease.reference_number")
    vuokralaiset_tyypit = serializers.SerializerMethodField()
    vuokralaiset_nimet = serializers.SerializerMethodField()
    vuokralaiset_osoitteet = serializers.CharField(source="tenants_contact_addresses")
    yhteyshenkilot_tyypit = serializers.SerializerMethodField()
    yhteyshenkilot_nimet = serializers.SerializerMethodField()
    yhteyshenkilot_osoitteet = serializers.CharField(
        source="contacts_contact_addresses"
    )
    ensisijainen_osoite = serializers.CharField(source="first_primary_address")
    vuokraus_alkupvm = serializers.DateField(source="lease.start_date")
    vuokraus_loppupvm = serializers.DateField(source="lease.end_date")
    irtisanomisaika = serializers.CharField(
        source="lease.notice_period.name", allow_null=True
    )
    vuokraus_kayttotarkoitus = serializers.CharField(
        source="lease.intended_use.name", allow_null=True
    )
    vuokraus_voimassa = serializers.SerializerMethodField()
    vuokraus_tila = serializers.CharField(source="lease.state", allow_null=True)
    pintaala = serializers.IntegerField(source="area")
    leikkauspintaala = serializers.IntegerField(source="section_area")
    # This value is always null, it is not filled in currently in db
    # Sum is annotated to the queryset in the view
    perittava_vuokra_summa = serializers.DecimalField(
        source="payable_rent_amount", max_digits=10, decimal_places=2
    )
    perittava_vuokra_jakso = serializers.SerializerMethodField()
    vuokraus_huom = serializers.CharField(
        source="lease.intended_use_note", allow_null=True
    )
    vuokraus_tyyppi = serializers.CharField(source="lease.type.name", allow_null=True)
    sijainti = serializers.CharField(source="location")
    geometria = serializers.SerializerMethodField(
        source="lease_area.geometry", read_only=True
    )
    palvelukokonaisuus = serializers.SerializerMethodField()
    border_hex_color = serializers.CharField(
        source="lease.service_unit.hex_color", allow_null=True, allow_blank=True
    )
    vuokranantaja = serializers.SerializerMethodField()
    tree_ids = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    alueen_tyyppi = serializers.CharField(source="type")
    valmistelija = serializers.SerializerMethodField()
    vuokraus_valmisteilla = serializers.SerializerMethodField()

    class Meta:
        model = LeaseArea
        fields = [
            "vuokraus_id",
            "kiinteistotunnus",
            "tyypin_tunnus",
            "vuokraustunnus",
            "sopimusnumero",
            "sopimus_allekirjoitettu",
            "vuokraus_diaari",
            "vuokralaiset_tyypit",
            "vuokralaiset_nimet",
            "vuokralaiset_osoitteet",
            "yhteyshenkilot_tyypit",
            "yhteyshenkilot_nimet",
            "yhteyshenkilot_osoitteet",
            "ensisijainen_osoite",
            "vuokraus_alkupvm",
            "vuokraus_loppupvm",
            "irtisanomisaika",
            "vuokraus_kayttotarkoitus",
            "vuokraus_voimassa",
            "vuokraus_tila",
            "pintaala",
            "leikkauspintaala",
            "perittava_vuokra_summa",
            "perittava_vuokra_jakso",
            "vuokraus_huom",
            "vuokraus_tyyppi",
            "sijainti",
            "geometria",
            "palvelukokonaisuus",
            "border_hex_color",
            "vuokranantaja",
            "tree_ids",
            "created_at",
            "alueen_tyyppi",
            "valmistelija",
            "vuokraus_valmisteilla",
        ]
        # Make all fields read only
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.now_date = timezone.now().date()

    def to_representation(self, instance):
        # IMPORTANT: Force translation to Finnish
        with override("fi"):
            return super().to_representation(instance)

    def get_vuokralaiset_tyypit(self, lease_area: LeaseArea):
        contact_types = lease_area.tenants_contact_types
        type_mapping = {
            "person": "Henkilö",
            "business": "Yritys",
            "unit": "Yksikkö",
            "association": "Yhteisö",
            "other": "Muu",
        }

        translated_types = [
            type_mapping.get(contact_type.value, None) for contact_type in contact_types
        ]
        return ", ".join(filter(None, translated_types))

    def get_vuokralaiset_nimet(self, lease_area: LeaseArea):
        contact_ids = lease_area.tenants_contact_ids
        contacts = Contact.objects.filter(id__in=contact_ids)
        names = [contact.get_name() for contact in contacts]

        return ", ".join(filter(None, names))

    def get_yhteyshenkilot_tyypit(self, lease_area: LeaseArea):
        contact_types = lease_area.contacts_contact_types

        type_mapping = {
            "person": "Henkilö",
            "business": "Yritys",
            "unit": "Yksikkö",
            "association": "Yhteisö",
            "other": "Muu",
        }

        translated_types = [
            type_mapping.get(contact_type.value, None) for contact_type in contact_types
        ]
        return ", ".join(filter(None, translated_types))

    def get_yhteyshenkilot_nimet(self, lease_area: LeaseArea):
        contact_ids = lease_area.contacts_contact_ids

        contacts = Contact.objects.filter(id__in=contact_ids)
        names = [contact.get_name() for contact in contacts]

        return ", ".join(filter(None, names))

    def get_vuokraus_voimassa(self, lease_area: LeaseArea):
        start_date = lease_area.lease.start_date
        end_date = lease_area.lease.end_date
        is_active = (end_date is None or end_date > self.now_date) and (
            start_date is not None
        )
        return "kyllä" if is_active else "ei"

    def get_perittava_vuokra_jakso(self, lease_area: LeaseArea):
        latest_payable_rent_start_date = lease_area.latest_payable_rent_start_date
        latest_payable_rent_end_date = lease_area.latest_payable_rent_end_date
        if any([latest_payable_rent_start_date, latest_payable_rent_end_date]):
            start_date = (
                latest_payable_rent_start_date.strftime("%d.%m.%Y")
                if latest_payable_rent_start_date
                else ""
            )
            end_date = (
                latest_payable_rent_end_date.strftime("%d.%m.%Y")
                if latest_payable_rent_end_date
                else ""
            )
            return f"{start_date} - {end_date}".strip()
        return ""

    def get_geometria(self, lease_area: LeaseArea):
        if lease_area.geometry:
            geom = GEOSGeometry(lease_area.geometry)
            geom.transform(3879)  # Transform to SRID 3879
            return json.loads(geom.json)
        return None

    def get_palvelukokonaisuus(self, lease_area: LeaseArea):
        service_unit_name = lease_area.lease.service_unit.name
        service_unit_mapping = {
            "Maaomaisuuden kehittäminen ja tontit": "MAKE/Tontit",
            "Alueiden käyttö ja valvonta": "AKV",
            "KuVa / Liikuntapaikkapalvelut": "KUVA (LIPA)",
            "KuVa / Ulkoilupalvelut": "KUVA (UPA)",
            "KuVa / Nuorisopalvelut": "KUVA (NUP)",
        }
        return service_unit_mapping.get(service_unit_name, None)

    def get_vuokranantaja(self, lease_area: LeaseArea):
        lessor: Contact = lease_area.lease.lessor
        if lessor:
            return lessor.get_name()
        return ""

    def get_tree_ids(self, lease_area: LeaseArea):
        return VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)

    def get_valmistelija(self, lease_area: LeaseArea) -> str:
        preparer: User | None = lease_area.lease.preparer
        return f"{preparer.first_name} {preparer.last_name}" if preparer else ""

    def get_vuokraus_valmisteilla(self, lease_area: LeaseArea) -> str:
        """Is lease in preparation?

        Note: Different from the UI field "Olotila" in the lease banner, which
        is only "Valmisteilla" if start date is null.
        """
        start_date = lease_area.lease.start_date
        return "kyllä" if (not start_date or start_date > self.now_date) else "ei"


class ExportVipunenMapLayerSerializer(serializers.ModelSerializer):
    tree_id = serializers.IntegerField(source="id")
    parent_tree_id = serializers.IntegerField(source="parent_id", allow_null=True)
    name_fi = serializers.CharField()
    name_sv = serializers.CharField(allow_null=True)
    name_en = serializers.CharField(allow_null=True)
    keywords = serializers.CharField(allow_null=True)
    hex_color = serializers.CharField(allow_null=True)

    class Meta:
        model = VipunenMapLayer
        fields = [
            "tree_id",
            "parent_tree_id",
            "name_fi",
            "name_sv",
            "name_en",
            "keywords",
            "hex_color",
        ]
        read_only_fields = fields


class ExportExpiredLeaseSerializer(serializers.ModelSerializer):
    vuokraustunnus = serializers.CharField(source="identifier.identifier")
    vuokraus_loppupvm = serializers.DateField(source="end_date")
    poistettu = serializers.SerializerMethodField()

    class Meta:
        model = Lease
        fields = [
            "vuokraustunnus",
            "vuokraus_loppupvm",
            "poistettu",
        ]
        read_only_fields = fields

    def get_poistettu(self, instance: Lease):
        if instance.deleted is not None:
            return "kyllä"
        return "ei"
