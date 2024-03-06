from typing import Union
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.metadata import SimpleMetadata
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audittrail.forms import AuditTrailSearchForm
from audittrail.serializers import LogEntrySerializer
from leasing.models import Contact, Lease
from audittrail.utils import recursive_get_related
from plotsearch.models import AreaSearch


TYPE_MAP = {
    "lease": {
        "model": Lease,
        "permission": "leasing.view_lease",
        "error_message": "Lease does not exist",
        "exclude_apps": ["forms", "plotsearch"],
    },
    "contact": {
        "model": Contact,
        "permission": "leasing.view_contact",
        "error_message": "Contact does not exist",
    },
    "areasearch": {
        "model": AreaSearch,
        "permission": "plotsearch.view_areasearch",
        "error_message": "Area search does not exist",
    },
}


def get_object(model, id) -> Union[Lease, Union[Contact, AreaSearch]]:
    try:
        if model is Lease:
            return Lease.objects.full_select_related_and_prefetch_related().get(pk=id)
        else:
            return model.objects.get(pk=id)
    except model.DoesNotExist:
        raise APIException(f"{model.__name__} does not exist")


class AuditTrailView(APIView):
    metadata_class = SimpleMetadata
    permission_classes = (IsAuthenticated,)

    def get_view_name(self):
        return _("View auditlog")

    def get_view_description(self, html=False):
        return _("View auditlog of a lease or a contact")

    def get(self, request, format=None):  # NOQA: C901
        search_form = AuditTrailSearchForm(self.request.query_params)
        if not search_form.is_valid():
            return Response(search_form.errors, status=status.HTTP_400_BAD_REQUEST)

        type_value = search_form["type"].value()

        if type_value not in TYPE_MAP:
            raise APIException("Invalid type")

        if not request.user.has_perm(TYPE_MAP[type_value]["permission"]):
            raise PermissionDenied()

        model = TYPE_MAP[type_value]["model"]
        id = search_form["id"].value()

        obj = get_object(model, id)

        exclude_apps = TYPE_MAP[type_value].get("exclude_apps", None)
        collected_items = recursive_get_related(
            obj, user=request.user, exclude_apps=exclude_apps
        )

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
        for field_name, field in AuditTrailSearchForm().fields.items():
            metadata["actions"]["GET"][field_name] = {
                "type": "field",
                "required": field.required,
                "read_only": False,
                "label": field.label,
            }
            if hasattr(field, "choices") and type(field.choices) is list:
                metadata["actions"]["GET"][field_name]["choices"] = [
                    {"value": value, "display_name": display_name}
                    for value, display_name in field.choices
                ]

        return Response(metadata, status=status.HTTP_200_OK)
