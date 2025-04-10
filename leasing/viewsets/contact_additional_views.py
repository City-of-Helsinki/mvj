import re

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.models import Contact
from leasing.permissions import PerMethodPermission


class ContactExistsView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"GET": ["leasing.view_contact"]}

    def get_view_name(self):
        return _("Check if contact already exist")

    def get_view_description(self, html=False):
        return _(
            "Check if contact already exist by business id or national identification number"
        )

    def get(self, request, format=None):
        identifier = request.query_params.get("identifier", None)
        # Optional, some integrations can use the endpoint with just identifier.
        service_unit_id = request.query_params.get("service_unit", None)
        if not identifier:
            raise APIException(_('Query parameter "identifier" is mandatory'))

        if re.match(r"FI\d{8}", identifier, re.IGNORECASE):
            identifier = "{}-{}".format(identifier[2:9], identifier[-1])

        contacts_qs = Contact.objects.filter(
            Q(business_id__iexact=identifier)
            | Q(national_identification_number__iexact=identifier)
        )
        if service_unit_id is not None:
            contacts_qs = contacts_qs.filter(service_unit_id=service_unit_id)

        return Response({"exists": contacts_qs.exists()})
