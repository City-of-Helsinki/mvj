from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.metadata import SimpleMetadata
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.forms import AuditLogSearchForm
from leasing.models import Contact, Lease
from leasing.models.utils import recursive_get_related
from leasing.serializers.auditlog import LogEntrySerializer


class AuditLogView(APIView):
    metadata_class = SimpleMetadata
    permission_classes = (IsAuthenticated,)

    def get_view_name(self):
        return _("View auditlog")

    def get_view_description(self, html=False):
        return _("View auditlog of a lease or a contact")

    def get(self, request, format=None):  # NOQA C901
        search_form = AuditLogSearchForm(self.request.query_params)
        if not search_form.is_valid():
            return Response(search_form.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.has_perm(
            "leasing.view_{}".format(search_form["type"].value())
        ):
            raise PermissionDenied()

        if search_form["type"].value() == "lease":
            try:
                obj = Lease.objects.full_select_related_and_prefetch_related().get(
                    pk=search_form["id"].value()
                )
            except Lease.DoesNotExist:
                raise APIException("Lease does not exist")
        elif search_form["type"].value() == "contact":
            try:
                obj = Contact.objects.get(pk=search_form["id"].value())
            except Lease.DoesNotExist:
                raise APIException("Contact does not exist")

        collected_items = recursive_get_related(obj, user=request.user)

        obj_content_type = ContentType.objects.get_for_model(obj)
        q = Q(content_type=obj_content_type) & Q(object_id=obj.id)
        for content_type, items in collected_items.items():
            q |= Q(content_type=content_type) & Q(object_id__in=[i.pk for i in items])

        queryset = (
            LogEntry.objects.filter(q)
            .distinct()
            .order_by("-timestamp")
            .select_related("actor")
        )

        serializer_context = {"request": request, "format": format, "view": self}

        paginator = LimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = LogEntrySerializer(page, many=True, context=serializer_context)
            return paginator.get_paginated_response(serializer.data)

        serializer = LogEntrySerializer(queryset, many=True, context=serializer_context)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        metadata_class = self.metadata_class()
        metadata = metadata_class.determine_metadata(request, self)
        metadata["actions"] = {"GET": {}}
        for field_name, field in AuditLogSearchForm().fields.items():
            metadata["actions"]["GET"][field_name] = {
                "type": "field",
                "required": field.required,
                "read_only": False,
                "label": field.label,
            }
            if hasattr(field, "choices") and type(field.choices) == list:
                metadata["actions"]["GET"][field_name]["choices"] = [
                    {"value": c[0], "display_name": c[1]} for c in field.choices
                ]

        return Response(metadata, status=status.HTTP_200_OK)
