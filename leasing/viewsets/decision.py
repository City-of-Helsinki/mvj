from copy import deepcopy

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import DecisionFilter
from leasing.models import Decision, Lease
from leasing.permissions import PerMethodPermission
from leasing.serializers.decision import (
    DecisionCreateUpdateSerializer,
    DecisionSerializer,
)

from .utils import AtomicTransactionModelViewSet


class DecisionViewSet(FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = Decision.objects.all()
    serializer_class = DecisionSerializer
    filterset_class = DecisionFilter

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DecisionCreateUpdateSerializer

        return DecisionSerializer


def get_decision_from_query_params(query_params):
    if not query_params.get("decision"):
        raise APIException("decision parameter is mandatory")

    try:
        return Decision.objects.get(pk=int(query_params.get("decision")))
    except Decision.DoesNotExist:
        raise APIException("Decision does not exist")
    except ValueError:
        raise APIException("Invalid decision id")


class DecisionCopyToLeasesView(APIView):
    permission_classes = (PerMethodPermission,)
    perms_map = {"POST": ["leasing.add_decision"]}

    def get_view_name(self):
        return _("Copy decision to leases")

    def get_view_description(self, html=False):
        return _("Duplicates chosen decision to chosen leases")

    def post(self, request, format=None):
        """
        We accept the following query parameters:
            ?decision=... - integer id of the decision to be copied
            ?leases=...&leases=... - integer ids of leases to copy decision to
            ?copy_conditions=1 - if we want the conditions to be copied as well
        """
        decision = get_decision_from_query_params(request.query_params)

        target_leases = request.query_params.getlist("leases")

        if not target_leases:
            raise APIException(
                'Please provide target lease ids with "leases" parameter'
            )

        for target_lease_id in target_leases:
            try:
                lease = Lease.objects.get(id=int(target_lease_id))
            except Lease.DoesNotExist:
                # TODO: report failed ids
                continue
            except ValueError:
                continue

            copied_decision = deepcopy(decision)
            copied_decision.pk = None
            copied_decision.lease = lease
            copied_decision.save()

            if request.query_params.get("copy_conditions"):
                for condition in decision.conditions.all():
                    copied_condition = condition
                    copied_condition.pk = None
                    copied_condition.decision = copied_decision
                    copied_condition.save()

        return Response({"success": True})
