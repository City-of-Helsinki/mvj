from unittest.mock import Mock

from landuse.models.party import AgreementParty
from landuse.permissions import check_collection_permissions


def test_authorized_collection_replacement_checks_each_operation():
    user = Mock()
    user.has_perm.return_value = True

    check_collection_permissions(user, AgreementParty, {1, 2}, [{"id": 1}, {}])

    assert {call.args[0] for call in user.has_perm.call_args_list} == {
        "landuse.add_agreementparty",
        "landuse.change_agreementparty",
        "landuse.delete_agreementparty",
    }
