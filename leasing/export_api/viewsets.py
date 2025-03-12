from django.contrib.postgres.aggregates import ArrayAgg, StringAgg
from django.db.models import OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token as TokenAuthenticationModel
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from leasing.enums import TenantContactType
from leasing.export_api.serializers import (
    ExportLeaseAreaSerializer,
    ExportVipunenMapLayerSerializer,
)
from leasing.models.contract import Contract
from leasing.models.land_area import LeaseArea, LeaseAreaAddress
from leasing.models.map_layers import VipunenMapLayer
from leasing.models.rent import Rent
from leasing.models.tenant import TenantContact


class CreatedAtCursorPagination(CursorPagination):
    ordering = "-created_at"
    page_size = 100


class ExportLeaseAreaPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_area")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_area")
        )


class ExportVipunenMapLayerPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_vipunen_map_layer")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_vipunen_map_layer")
        )


class ExportLeaseAreaViewSet(ReadOnlyModelViewSet):
    authentication_classes = [TokenAuthentication]
    pagination_class = CreatedAtCursorPagination
    permission_classes = [
        IsAuthenticated,
        ExportLeaseAreaPermission,
    ]
    serializer_class = ExportLeaseAreaSerializer

    def get_queryset(self):
        now = timezone.now()

        tenants_contact_ids_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.TENANT,
            )
            .values("tenant__lease")
            .annotate(contact_ids=ArrayAgg("contact_id", distinct=True))
            .values("contact_ids")
        )

        tenants_contact_types_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.TENANT,
            )
            .values("tenant__lease")
            .annotate(
                contact_types=Coalesce(ArrayAgg("contact__type", distinct=True), [])
            )
            .values("contact_types")
        )

        tenants_contact_addresses_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.TENANT,
            )
            .values("tenant__lease")
            .annotate(
                contact_addresses=Coalesce(
                    StringAgg("contact__address", distinct=True, delimiter=", "), []
                )
            )
            .values("contact_addresses")
        )

        contacts_contact_ids_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.CONTACT,
            )
            .values("tenant__lease")
            .annotate(contact_ids=ArrayAgg("contact_id", distinct=True))
            .values("contact_ids")
        )

        contacts_contact_types_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.CONTACT,
            )
            .values("tenant__lease")
            .annotate(
                contact_types=Coalesce(ArrayAgg("contact__type", distinct=True), [])
            )
            .values("contact_types")
        )

        contacts_contact_address_subquery = (
            TenantContact.objects.filter(
                Q(end_date__isnull=True) | Q(end_date__gt=now),
                tenant__lease=OuterRef("lease"),
                type=TenantContactType.CONTACT,
            )
            .values("tenant__lease")
            .annotate(
                contact_addresses=Coalesce(
                    StringAgg("contact__address", distinct=True, delimiter=", "), []
                )
            )
            .values("contact_addresses")
        )

        latest_rent_subquery = Rent.objects.filter(lease=OuterRef("lease")).order_by(
            "-payable_rent_start_date"
        )

        qs = (
            LeaseArea.objects.filter(
                archived_at__isnull=True,
                deleted__isnull=True,
                lease__deleted__isnull=True,
            )
            .filter(Q(lease__end_date__isnull=True) | Q(lease__end_date__gt=now))
            .annotate(
                tenants_contact_ids=Coalesce(
                    Subquery(tenants_contact_ids_subquery), []
                ),
                tenants_contact_types=Coalesce(
                    Subquery(tenants_contact_types_subquery), []
                ),
                tenants_contact_addresses=Subquery(tenants_contact_addresses_subquery),
                contacts_contact_ids=Coalesce(
                    Subquery(contacts_contact_ids_subquery), []
                ),
                contacts_contact_types=Coalesce(
                    Subquery(contacts_contact_types_subquery), []
                ),
                contacts_contact_addresses=Subquery(contacts_contact_address_subquery),
            )
            .annotate(
                payable_rent_amount=Sum("lease__rents__payable_rent_amount"),
                latest_contract_number=Subquery(
                    Contract.objects.filter(lease=OuterRef("lease"))
                    .order_by("-id")
                    .values("contract_number")[:1]
                ),
                latest_signing_date=Subquery(
                    Contract.objects.filter(lease=OuterRef("lease"))
                    .order_by("-id")
                    .values("signing_date")[:1]
                ),
                latest_payable_rent_start_date=Subquery(
                    latest_rent_subquery.values("payable_rent_start_date")[:1]
                ),
                latest_payable_rent_end_date=Subquery(
                    latest_rent_subquery.values("payable_rent_end_date")[:1]
                ),
            )
            .annotate(
                first_primary_address=Subquery(
                    LeaseAreaAddress.objects.filter(
                        lease_area=OuterRef("pk"), is_primary=True
                    )
                    .order_by("-id")
                    .values("address_fi")[:1]
                ),
            )
            .select_related(
                "lease",
                "lease__service_unit",
                "lease__type",
                "lease__identifier",
                "lease__lessor",
                "lease__intended_use",
                "lease__notice_period",
            )
            .prefetch_related(
                "lease__tenants",
                "lease__tenants__contacts",
            )
        )
        return qs


class ExportVipunenMapLayerViewSet(ReadOnlyModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [
        IsAuthenticated,
        ExportVipunenMapLayerPermission,
    ]
    serializer_class = ExportVipunenMapLayerSerializer
    queryset = VipunenMapLayer.objects.all()
