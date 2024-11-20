import pytest
from django.db.models.deletion import ProtectedError

from gdpr.utils import delete_user_data
from plotsearch.enums import InformationCheckName


@pytest.mark.django_db
def test_delete_user_data(
    user_factory,  # users
    area_search_factory,  # plotsearch
    area_search_attachment_factory,  # plotsearch
    favourite_factory,
    answer_factory,  # form
    attachment_factory,  # form
):
    user = user_factory()
    areasearch = area_search_factory(user=user, description_area="Test")
    areasearch_attachment = area_search_attachment_factory(
        user=user, area_search=areasearch
    )
    favourite = favourite_factory(user=user)
    answer = answer_factory(user=user)
    attachment = attachment_factory(user=user)

    assert areasearch.user == user
    delete_user_data(user, dry_run=False)

    # The following have `on_delete=models.SET_NULL`.
    # It is expected that the user field is set to None.
    areasearch.refresh_from_db()
    assert areasearch.user is None
    areasearch_attachment.refresh_from_db()
    assert areasearch_attachment.user is None
    answer.refresh_from_db()
    assert answer.user is None
    attachment.refresh_from_db()
    assert attachment.user is None

    # on_delete=models.CASCADE -> expect model instance to be deleted
    with pytest.raises(favourite.DoesNotExist):
        favourite.refresh_from_db()


@pytest.mark.django_db
def test_delete_user_data_not_possible(
    user_factory,  # users
    information_check_factory,  # plotsearch
):
    user = user_factory()
    # IMPORTANT: This model is not expected to be related to a user that would be doing
    # a GDPR API delete. It is used simply for demonstration purposes, as the model
    # has `on_delete=models.PROTECT` for the `preparer` field that refers to a `User` instance.
    information_check = information_check_factory(
        preparer=user, name=InformationCheckName.CREDITWORTHINESS
    )
    # on_delete=models.PROTECT -> expect deletion not to be possible
    with pytest.raises(ProtectedError):
        delete_user_data(user, dry_run=False)

    assert information_check.preparer == user
