from django.utils import timezone
from rest_framework.serializers import ValidationError

from leasing.enums import PlotSearchTargetType


class PlotSearchTargetAddValidator:
    """
    Check that "searchable" -type plot search targets are not added/edited after plot search has begun
    """

    def __call__(self, value):
        targets = value.pop("plot_search_targets", [])
        for target in targets:
            if "id" in target:
                continue
            begin_is_past = timezone.now() > value["begin_at"]
            if (
                target["target_type"] == PlotSearchTargetType.SEARCHABLE
                and begin_is_past
            ):
                raise ValidationError(
                    code="no_adding_searchable_targets_after_begins_at"
                )
