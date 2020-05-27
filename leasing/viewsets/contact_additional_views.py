import re

from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
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
        if not identifier:
            raise APIException(_('Query parameter "identifier" is mandatory'))

        if re.match(r"FI\d{8}", identifier, re.IGNORECASE):
            identifier = "{}-{}".format(identifier[2:9], identifier[-1])

        return Response(
            {
                "exists": Contact.objects.filter(
                    Q(business_id__iexact=identifier)
                    | Q(national_identification_number__iexact=identifier)
                ).exists()
            }
        )
