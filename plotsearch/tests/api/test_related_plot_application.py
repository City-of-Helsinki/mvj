import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from plotsearch.models import InformationCheck, PlotSearch, RelatedPlotApplication


@pytest.mark.django_db
class TestRelatedPlotApplicationViews:
    def test_list_related_plot_applications(
        self, admin_client, related_plot_application_factory
    ):
        related_plot_applications = related_plot_application_factory.create_batch(10)
        url = reverse("v1:related_plot_application-list")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_results_count = len(response.data.get("results", []))
        objects_count = len(related_plot_applications)
        assert response_results_count == objects_count

    def test_retrieve_related_plot_application(
        self, admin_client, related_plot_application_test_data
    ):
        related_plot_applications = related_plot_application_test_data[
            "related_plot_applications"
        ]
        for related_plot_application in related_plot_applications:
            url = reverse(
                "v1:related_plot_application-detail", args=[related_plot_application.id]
            )
            response = admin_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data["id"] == related_plot_application.id

    def test_create_related_plot_application(
        self, admin_client, related_plot_application_test_data
    ):
        url = reverse("v1:related_plot_application-list")
        data = {
            "lease": related_plot_application_test_data["lease"].id,
            "content_type_model": ContentType.objects.get_for_model(
                related_plot_application_test_data["area_search"]
            ).model,
            "object_id": related_plot_application_test_data["area_search"].id,
        }
        response = admin_client.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert RelatedPlotApplication.objects.filter(id=response.data["id"]).exists()

    def test_create_related_plot_application_permissions(
        self, client, user, related_plot_application_test_data
    ):
        url = reverse("v1:related_plot_application-list")
        data = {
            "lease": related_plot_application_test_data["lease"].id,
            "content_type_model": ContentType.objects.get_for_model(
                related_plot_application_test_data["area_search"]
            ).model,
            "object_id": related_plot_application_test_data["area_search"].id,
        }

        client.force_login(user)
        response = client.post(url, data=data)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Anonymous user should not be able to create"

        permission = Permission.objects.get(codename="add_relatedplotapplication")
        user.user_permissions.add(permission)
        client.force_login(user)
        response = client.post(url, data=data)
        assert (
            response.status_code == status.HTTP_201_CREATED
        ), "Create permission should allow user to create"
        assert RelatedPlotApplication.objects.filter(id=response.data["id"]).exists()

    def test_create_related_plot_application_validation(
        self, admin_client, related_plot_application_test_data
    ):
        url = reverse("v1:related_plot_application-list")
        data_incorrect_model = {
            "lease": related_plot_application_test_data["lease"].id,
            "content_type_model": ContentType.objects.get_for_model(
                InformationCheck
            ).model,
            "object_id": related_plot_application_test_data["area_search"].id,
        }
        data_non_existing_object = {
            "lease": related_plot_application_test_data["lease"].id,
            "content_type_model": ContentType.objects.get_for_model(
                related_plot_application_test_data["area_search"]
            ).model,
            "object_id": 12345,
        }

        response = admin_client.post(url, data=data_incorrect_model)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["content_type_model"][0].code == "invalid_choice"

        response = admin_client.post(url, data=data_non_existing_object)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["non_field_errors"][0].code == "invalid"

    def test_delete_related_plot_application(
        self, admin_client, related_plot_application_test_data
    ):
        related_plot_application = related_plot_application_test_data[
            "related_plot_applications"
        ].pop()
        url = reverse(
            "v1:related_plot_application-detail", args=[related_plot_application.id]
        )
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not RelatedPlotApplication.objects.filter(
            id=related_plot_application.id
        ).exists()

    def test_delete_related_plot_application_permissions(
        self, client, user, related_plot_application_test_data
    ):
        related_plot_application = related_plot_application_test_data[
            "related_plot_applications"
        ].pop()
        url = reverse(
            "v1:related_plot_application-detail", args=[related_plot_application.id]
        )

        client.force_login(user)
        response = client.delete(url)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), "Anonymous user should not be able to delete"

        permission = Permission.objects.get(codename="delete_relatedplotapplication")
        user.user_permissions.add(permission)
        client.force_login(user)
        response = client.delete(url)
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), "Delete permission should allow user to delete"
        assert not RelatedPlotApplication.objects.filter(
            id=related_plot_application.id
        ).exists()

    def test_create_related_plot_application_content_type_choices(
        self, admin_client, lease_factory, plot_search_factory
    ):
        url = reverse("v1:related_plot_application-list")
        data = {
            "lease": lease_factory().id,
            "content_type": ContentType.objects.get_for_model(PlotSearch).id,
            "object_id": plot_search_factory().id,
        }
        response = admin_client.post(url, data=data)
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), "Should not allow unlisted ContentType"
