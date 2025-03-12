import pytest

from leasing.models.map_layers import VipunenMapLayer


@pytest.mark.django_db
def test_get_map_layer_ids_for_lease_area(
    lease_factory,
    lease_area_factory,
    vipunen_map_layer_factory,
    lease_type_factory,
    intended_use_factory,
):
    lease_type = lease_type_factory()
    lease = lease_factory(type=lease_type)
    lease_area = lease_area_factory(lease=lease)

    root_layer = vipunen_map_layer_factory()
    tree_ids = VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)
    # Should have no layers
    assert len(tree_ids) == 0
    child_layer = vipunen_map_layer_factory(parent=root_layer, lease_type=lease_type)
    tree_ids = VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)
    # Should have one layer via LeaseType
    assert child_layer.id in tree_ids
    child_layer2 = vipunen_map_layer_factory(parent=root_layer, lease_type=lease_type)
    tree_ids = VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)
    # Should have two layers via LeaseType
    assert child_layer2.id in tree_ids
    assert child_layer.id in tree_ids
    child_child_layer = vipunen_map_layer_factory(
        parent=child_layer, lease_type=lease_type
    )
    tree_ids = VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)
    # Should have three layers via LeaseType, with one child having a child as parent
    assert child_child_layer.id in tree_ids
    assert child_layer2.id in tree_ids
    assert child_layer.id in tree_ids
    intended_use = intended_use_factory(service_unit=lease.service_unit)
    lease.intended_use = intended_use
    lease.save()
    child_child_layer.intended_use = intended_use
    child_child_layer.lease_type = None
    child_child_layer.save()
    tree_ids = VipunenMapLayer.get_map_layer_ids_for_lease_area(lease_area)
    # Should have child_child_layer via IntendedUse
    assert child_child_layer.id in tree_ids
