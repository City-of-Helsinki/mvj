import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from leasing.enums import PlotSearchTargetType
from plotsearch.serializers import (
    PlotSearchRetrieveSerializer,
    PlotSearchUpdateSerializer,
)


@pytest.mark.django_db
def test_plot_search_validation(
    django_db_setup, plot_search_test_data, plan_unit_factory, lease_test_data
):
    plan_unit = plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    plot_search_target_data = {
        "plan_unit_id": plan_unit.id,
        "target_type": PlotSearchTargetType.SEARCHABLE,
    }

    data = PlotSearchRetrieveSerializer(plot_search_test_data).data
    data["plot_search_targets"].append(plot_search_target_data)
    data["begin_at"] = (timezone.now() - timezone.timedelta(days=30)).replace(
        microsecond=0
    )
    data["end_at"] = (data["begin_at"] + timezone.timedelta(days=30)).replace(
        microsecond=0
    )
    pl_update_serializer = PlotSearchUpdateSerializer(data=data)
    with pytest.raises(ValidationError) as val_error:
        pl_update_serializer.update(plot_search_test_data, data)
    assert (
        val_error.value.detail[0].code == "no_adding_searchable_targets_after_begins_at"
    )

    data = PlotSearchRetrieveSerializer(plot_search_test_data).data
    # reverse-test
    plot_search_target_data = {
        "plan_unit_id": plan_unit.id,
        "target_type": PlotSearchTargetType.SEARCHABLE,
    }
    data["begin_at"] = timezone.now() + timezone.timedelta(days=30)
    data["end_at"] = data["begin_at"] + timezone.timedelta(days=30)
    data["plot_search_targets"].append(plot_search_target_data)
    pl_update_serializer = PlotSearchUpdateSerializer(data=data)
    assert pl_update_serializer.update(plot_search_test_data, data)
