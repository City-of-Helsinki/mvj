import datetime
import json
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType, InvoiceState, InvoiceType, PlotType
from leasing.models import (
    LandUseAgreement,
    LandUseAgreementInvoice,
    LandUseAgreementInvoiceRow,
)
from leasing.serializers.land_use_agreement import LandUseAgreementAttachmentSerializer
from leasing.utils import calculate_increase_with_360_day_calendar


def test_list_land_use_agreements(
    django_db_setup, admin_client, land_use_agreement_test_data
):

    url = reverse("landuseagreement-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_get_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data
):
    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    assert response.data.get("id") == land_use_agreement_test_data.id
    assert response.data.get("type") == land_use_agreement_test_data.type_id
    assert (
        response.data.get("preparer").get("username")
        == land_use_agreement_test_data.preparer.username
    )
    assert (
        response.data.get("land_use_contract_type")
        == land_use_agreement_test_data.land_use_contract_type.value
    )
    assert (
        response.data.get("plan_acceptor")
        == land_use_agreement_test_data.plan_acceptor.id
    )
    assert (
        response.data.get("estimated_completion_year")
        == land_use_agreement_test_data.estimated_completion_year
    )
    assert (
        response.data.get("estimated_introduction_year")
        == land_use_agreement_test_data.estimated_introduction_year
    )
    assert (
        response.data.get("project_area") == land_use_agreement_test_data.project_area
    )
    assert (
        response.data.get("plan_reference_number")
        == land_use_agreement_test_data.plan_reference_number
    )
    assert response.data.get("plan_number") == land_use_agreement_test_data.plan_number
    assert response.data.get(
        "plan_lawfulness_date"
    ) == land_use_agreement_test_data.plan_lawfulness_date.strftime("%Y-%m-%d")
    assert response.data.get("state") == land_use_agreement_test_data.state
    assert response.data.get("addresses")[0].get("address") == "Testikatu 1"
    assert response.data.get("contracts")[0].get("contract_number") == "A123"
    assert response.data.get("conditions")[0].get("obligated_area") == 1000
    assert response.data.get("decisions")[0].get("reference_number") == "1234"
    response_litigants = response.data.get("litigants")
    assert len(response_litigants) == 2
    contact_set = response_litigants[0].get("landuseagreementlitigantcontact_set")
    assert "Litigant First" in contact_set[0].get("contact")["first_name"]


@pytest.mark.django_db
def test_update_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )
    user = user_factory(username="test_user_2")

    data = {
        "id": land_use_agreement_test_data.id,
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "estates": ["TEST"],
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {"address": "Testikatu 2", "postal_code": "00100", "city": "Helsinki"}
        ],
    }
    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert response.data.get("addresses")[0].get("address") == "Testikatu 2"


@pytest.mark.django_db
def test_create_land_use_agreement(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse("landuseagreement-list")
    user = user_factory(username="test_user_2")

    data = {
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {"address": "Testikatu 1", "postal_code": "00100", "city": "Helsinki"}
        ],
    }
    response = admin_client.post(url, data=data, content_type="application/json")
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_land_use_agreement_w_two_addresses(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory,
):

    url = reverse("landuseagreement-list")
    user = user_factory(username="test_user_2")

    data = {
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "preparer": user.id,
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "addresses": [
            {
                "address": "Testikatu 1",
                "postal_code": "00100",
                "city": "Helsinki",
                "is_primary": True,
            },
            {
                "address": "Testikatu 666",
                "postal_code": "00100",
                "city": "Helsinki",
                "is_primary": False,
            },
        ],
    }
    response = admin_client.post(url, data=data, content_type="application/json")
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    assert len(response.data.get("addresses", [])) == 2


@pytest.mark.django_db
def test_land_use_agreement_retrieve_plots(
    admin_client,
    land_use_agreement_test_data,
    lease_factory,
    lease_area_factory,
    user_factory,
    plot_factory,
):
    # Initialize test data
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )
    lease_area = lease_area_factory(
        lease=lease, identifier="12345", area=1000, section_area=1000,
    )
    exist_plot_1 = plot_factory(
        identifier="12345",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )
    exist_plot_2 = plot_factory(
        identifier="678910",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )
    land_use_agreement_test_data.plots.add(exist_plot_1)
    land_use_agreement_test_data.plots.add(exist_plot_2)

    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data.get("plots", [])) == 2


@pytest.mark.django_db
def test_land_use_agreement_update_plots(
    admin_client,
    land_use_agreement_test_data,
    lease_factory,
    lease_area_factory,
    user_factory,
    plot_factory,
):
    # Initialize test data
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )
    lease_area = lease_area_factory(
        lease=lease, identifier="12345", area=1000, section_area=1000,
    )
    master_plot = plot_factory(
        identifier="12345",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
        is_master=True,
    )
    exist_plot = plot_factory(
        identifier="678910",
        area=1000,
        type=PlotType.REAL_PROPERTY,
        lease_area=lease_area,
    )
    land_use_agreement_test_data.plots.add(exist_plot)

    url = reverse(
        "landuseagreement-detail", kwargs={"pk": land_use_agreement_test_data.id}
    )

    data = {
        "id": land_use_agreement_test_data.id,
        "type": land_use_agreement_test_data.type.id,
        "status": land_use_agreement_test_data.status.id,
        "definition": land_use_agreement_test_data.definition.id,
        "municipality": land_use_agreement_test_data.municipality.id,
        "district": land_use_agreement_test_data.district.id,
        "plots": [{"id": exist_plot.id}, {"id": master_plot.id}],
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data.get("plots")) == 2
    assert response.data.get("plots")[1].get("id") != master_plot.id


def test_update_land_use_agreement_compensations_without_existing_data(
    django_db_setup, admin_client, land_use_agreement_test_data
):
    lua = land_use_agreement_test_data

    assert hasattr(lua, "compensations") is False

    url = reverse("landuseagreement-detail", kwargs={"pk": lua.id})

    data = {
        "id": lua.id,
        "type": lua.type.id,
        "status": lua.status.id,
        "definition": lua.definition.id,
        "municipality": lua.municipality.id,
        "district": lua.district.id,
        "compensations": {
            "cash_compensation": 123,
            "land_compensation": 123,
            "other_compensation": 123,
            "first_installment_increase": 123,
            "street_acquisition_value": 123,
            "street_area": 123,
            "unit_prices_used_in_calculation": [
                {
                    "usage": "test",
                    "management": "test",
                    "protected": "test",
                    "area": 1000,
                    "unit_value": 1000,
                    "discount": 10,
                    "used_price": 900,
                }
            ],
        },
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lua = LandUseAgreement.objects.get(pk=lua.id)
    assert lua.compensations.cash_compensation == Decimal(123)
    assert lua.compensations.land_compensation == Decimal(123)
    assert lua.compensations.other_compensation == Decimal(123)
    assert lua.compensations.first_installment_increase == Decimal(123)
    assert lua.compensations.street_acquisition_value == Decimal(123)
    assert lua.compensations.street_area == Decimal(123)

    assert lua.compensations.unit_prices_used_in_calculation.count() == 1
    assert lua.compensations.unit_prices_used_in_calculation.first().usage == "test"
    assert lua.compensations.unit_prices_used_in_calculation.first().used_price == Decimal(
        900
    )


def test_update_land_use_agreement_compensations(
    django_db_setup,
    admin_client,
    land_use_agreement_test_data,
    land_use_agreement_compensations_factory,
    land_use_agreement_compensations_unit_price_factory,
):
    lua = land_use_agreement_test_data

    # set the initial data
    lua.compensations = land_use_agreement_compensations_factory(
        land_use_agreement=lua,
        cash_compensation=100,
        land_compensation=100,
        other_compensation=100,
        first_installment_increase=100,
        street_acquisition_value=1000,
        park_acquisition_value=1000,
        other_acquisition_value=1000,
        street_area=1000,
        park_area=1000,
        other_area=1000,
    )
    lua.save()

    unit_prices = land_use_agreement_compensations_unit_price_factory(
        compensations=lua.compensations,
        usage="test",
        management="test",
        protected="test",
        area=500,
        unit_value=500,
        discount=20,
        used_price=400,
    )

    assert lua.compensations.unit_prices_used_in_calculation.count() == 1
    assert lua.compensations.unit_prices_used_in_calculation.first().used_price == Decimal(
        400
    )

    url = reverse("landuseagreement-detail", kwargs={"pk": lua.id})

    data = {
        "id": lua.id,
        "type": lua.type.id,
        "status": lua.status.id,
        "definition": lua.definition.id,
        "municipality": lua.municipality.id,
        "district": lua.district.id,
        "compensations": {
            "cash_compensation": 123,
            "land_compensation": 123,
            "other_compensation": 123,
            "first_installment_increase": 123,
            "street_acquisition_value": 123,
            "street_area": 123,
            "unit_prices_used_in_calculation": [
                {
                    "id": unit_prices.id,
                    "usage": "test",
                    "management": "test",
                    "protected": "test",
                    "area": 1000,
                    "unit_value": 1000,
                    "discount": 10,
                    "used_price": 900,
                }
            ],
        },
    }

    response = admin_client.put(url, data=data, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    lua = LandUseAgreement.objects.get(pk=lua.id)

    # compensations are updated correctly
    assert lua.compensations.cash_compensation == Decimal(123)
    assert lua.compensations.land_compensation == Decimal(123)
    assert lua.compensations.other_compensation == Decimal(123)
    assert lua.compensations.first_installment_increase == Decimal(123)
    assert lua.compensations.street_acquisition_value == Decimal(123)
    assert lua.compensations.street_area == Decimal(123)

    # unit prices are updated correctly
    assert lua.compensations.unit_prices_used_in_calculation.count() == 1
    assert lua.compensations.unit_prices_used_in_calculation.first().usage == "test"
    assert lua.compensations.unit_prices_used_in_calculation.first().used_price == Decimal(
        900
    )


def test_upload_attachment(
    django_db_setup, admin_client, land_use_agreement_test_data, user_factory
):
    lua = land_use_agreement_test_data

    assert lua.attachments.count() == 0

    url = reverse("landuseagreementattachment-list")

    data = {
        "type": "general",
        "land_use_agreement": lua.id,
    }

    dummy_file = BytesIO(b"dummy data")
    dummy_file.name = "dummy_file.pdf"

    response = admin_client.post(
        url, data={"data": json.dumps(data, cls=DjangoJSONEncoder), "file": dummy_file}
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    assert lua.attachments.count() == 1
    assert lua.attachments.first().uploader == response.wsgi_request.user


@pytest.mark.django_db
def test_download_attachment(
    django_db_setup, admin_client, client, land_use_agreement_test_data, user_factory
):
    lua = land_use_agreement_test_data
    user = user_factory(username="test_user")
    user.set_password("test_password")
    user.save()

    assert lua.attachments.count() == 0

    # upload a file first
    upload_url = reverse("landuseagreementattachment-list")
    data = {
        "type": "general",
        "land_use_agreement": lua.id,
    }

    dummy_file = BytesIO(b"dummy data")
    dummy_file.name = "dummy_file.pdf"

    response = admin_client.post(
        upload_url,
        data={"data": json.dumps(data, cls=DjangoJSONEncoder), "file": dummy_file},
    )
    assert response.status_code == 201, "{} {}".format(
        response.status_code, response.data
    )
    assert lua.attachments.count() == 1

    attachment = lua.attachments.first()
    attachment_serializer = LandUseAgreementAttachmentSerializer(attachment)

    download_url = attachment_serializer.get_file_url(attachment)

    # anonymous user should not be allowed to download the file
    response = client.get(download_url)
    assert response.status_code == 401, "{} {}".format(
        response.status_code, response.data
    )

    # logged in user without permissions should not be allowed to download the file
    client.login(username="test_user", password="test_password")
    response = client.get(download_url)
    assert response.status_code == 403, "{} {}".format(
        response.status_code, response.data
    )
    assert response.data["detail"].code == "permission_denied"

    # admin user should be allowed to download the file
    response = admin_client.get(download_url)
    assert response.status_code == 200, "{} {}".format(
        response.status_code, response.data
    )
    assert response.get("Content-Disposition").startswith(
        'attachment; filename="dummy_file'
    )
    assert response.content == b"dummy data"


def test_create_invoice(contact_factory, admin_client, land_use_agreement_test_data):
    recipient = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    plan_lawfulness_date = datetime.date(2020, 5, 8)
    sign_date = datetime.date(2020, 4, 8)
    expected_amount = calculate_increase_with_360_day_calendar(
        sign_date, plan_lawfulness_date, 3, 150000
    )

    data = {
        "land_use_agreement": land_use_agreement_test_data.id,
        "due_date": "2020-07-01",
        "recipient": recipient.id,
        "rows": [
            {
                "compensation_amount": 150000,
                "increase_percentage": 3,
                "plan_lawfulness_date": plan_lawfulness_date.isoformat(),
                "receivable_type": 1,
                "sign_date": sign_date.isoformat(),
            }
        ],
    }

    url = reverse("landuseagreementinvoice-list")
    response = admin_client.post(url, data=data, content_type="application/json",)

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.rows.count() > 0
    assert invoice.rows.first().amount == expected_amount

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == expected_amount
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_create_zero_sum_invoice_state_is_paid(
    contact_factory, admin_client, land_use_agreement_test_data
):
    recipient = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    plan_lawfulness_date = datetime.date(2020, 5, 8)
    sign_date = datetime.date(2020, 4, 8)

    data = {
        "land_use_agreement": land_use_agreement_test_data.id,
        "due_date": "2020-07-01",
        "recipient": recipient.id,
        "rows": [
            {
                "compensation_amount": 150000,
                "increase_percentage": 3,
                "plan_lawfulness_date": plan_lawfulness_date.isoformat(),
                "receivable_type": 1,
                "sign_date": sign_date.isoformat(),
            },
            {
                "compensation_amount": -150000,
                "increase_percentage": 3,
                "plan_lawfulness_date": plan_lawfulness_date.isoformat(),
                "receivable_type": 1,
                "sign_date": sign_date.isoformat(),
            },
        ],
    }

    url = reverse("landuseagreementinvoice-list")
    response = admin_client.post(url, data=data, content_type="application/json",)
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_get_invoice_list(admin_client, land_use_agreement_test_data):
    url = reverse("landuseagreementinvoice-list")
    response = admin_client.get(url, content_type="application/json",)
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data["results"]) > 0


@pytest.mark.django_db
def test_get_invoice_detail(admin_client, land_use_agreement_test_data):
    invoice_id = land_use_agreement_test_data.invoices.first().id

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice_id})
    response = admin_client.get(url, content_type="application/json",)
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_patch_invoice_change_one_row_amount(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123.45),
        billed_amount=Decimal(123.45),
        outstanding_amount=Decimal(123.45),
        recipient=contact,
    )

    invoice_row = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(1234567.89),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row.id,
                "receivable_type": invoice_row.receivable_type_id,
                "compensation_amount": 150000,
            }
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice_row = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row.id)

    assert invoice_row.amount == Decimal(151000.00)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.billed_amount == Decimal(151000.00)
    assert invoice.outstanding_amount == Decimal(151000.00)
    assert invoice.total_amount == Decimal(151000.00)


@pytest.mark.django_db
def test_patch_invoice_change_other_row_amount(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(250000),
        billed_amount=Decimal(250000),
        recipient=contact,
    )

    invoice_row1 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(150000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice_row2 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "compensation_amount": 150000,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "compensation_amount": 200000,
            },
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice_row1 = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row1.id)
    assert invoice_row1.amount == Decimal(151000.00)
    invoice_row2 = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row2.id)
    assert invoice_row2.amount == Decimal(201000.00)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.billed_amount == Decimal(352000.00)
    assert invoice.outstanding_amount == Decimal(352000.00)
    assert invoice.total_amount == Decimal(352000.00)


@pytest.mark.django_db
def test_patch_invoice_change_two_row_amount(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(250000),
        billed_amount=Decimal(250000),
        recipient=contact,
    )

    invoice_row1 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(150000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice_row2 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "amount": 150000,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "amount": 200000,
            },
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice_row1 = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row1.id)
    assert invoice_row1.amount == Decimal(151000.00)
    invoice_row2 = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row2.id)
    assert invoice_row2.amount == Decimal(100000.00)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.billed_amount == Decimal(251000.00)
    assert invoice.outstanding_amount == Decimal(251000.00)
    assert invoice.total_amount == Decimal(251000.00)


@pytest.mark.django_db
def test_patch_invoice_with_invoiceset_change_row_amount(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_set_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoiceset = land_use_agreement_invoice_set_factory(
        land_use_agreement=land_use_agreement
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350000),
        billed_amount=Decimal(250000),
        outstanding_amount=Decimal(250000),
        recipient=contact,
    )

    invoice_row1 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice_row2 = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(150000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice2 = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350000),
        billed_amount=Decimal(100000),
        outstanding_amount=Decimal(100000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        compensation_amount=Decimal(50000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        compensation_amount=Decimal(50000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "compensation_amount": 50000,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "compensation_amount": 60000,
            },
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.filter(pk=invoice.id).first()

    assert invoice.billed_amount == Decimal(110000.00)
    assert invoice.outstanding_amount == Decimal(110000.00)
    assert invoice.total_amount == Decimal(110000.00)

    invoice2 = LandUseAgreementInvoice.objects.get(pk=invoice2.id)

    assert invoice2.billed_amount == Decimal(100000.00)
    assert invoice2.outstanding_amount == Decimal(100000.00)
    assert invoice2.total_amount == Decimal(350000.00)


@pytest.mark.django_db
def test_delete_invoice_invoice_in_invoiceset(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_set_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoiceset = land_use_agreement_invoice_set_factory(
        land_use_agreement=land_use_agreement
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350000),
        billed_amount=Decimal(250000),
        outstanding_amount=Decimal(250000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(150000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice2 = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350000),
        billed_amount=Decimal(100000),
        outstanding_amount=Decimal(100000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        compensation_amount=Decimal(50000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        compensation_amount=Decimal(50000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice2.id})
    response = admin_client.delete(url, content_type="application/json")

    assert response.status_code == 204, "%s %s" % (response.status_code, response.data)

    with pytest.raises(LandUseAgreementInvoice.DoesNotExist):
        LandUseAgreementInvoice.objects.get(pk=invoice2.id)

    invoice = LandUseAgreementInvoice.objects.get(pk=invoice.id)

    assert invoice.billed_amount == Decimal(250000.00)
    assert invoice.outstanding_amount == Decimal(250000.00)
    assert invoice.total_amount == Decimal(350000.00)


@pytest.mark.django_db
def test_patch_invoice_change_if_sent_to_sap(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal("123456.78"),
        billed_amount=Decimal("123456.78"),
        outstanding_amount=Decimal("123456.78"),
        recipient=contact,
        due_date=datetime.date(year=2017, month=6, day=1),
        postpone_date=None,
        sent_to_sap_at=timezone.now(),
    )

    invoice_row = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(123456.78),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "due_date": datetime.date(year=2017, month=6, day=2),
        "postpone_date": datetime.date(year=2018, month=6, day=2),
        "rows": [
            {
                "id": invoice_row.id,
                "receivable_type": invoice_row.receivable_type_id,
                "compensation_amount": 100000,
            }
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice_row = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row.id)

    assert invoice_row.amount == Decimal("124000.00")

    invoice = LandUseAgreementInvoice.objects.get(pk=invoice.id)

    assert invoice.billed_amount == Decimal("124000.00")
    assert invoice.outstanding_amount == Decimal("124000.00")
    assert invoice.total_amount == Decimal("124000.00")
    assert invoice.postpone_date == datetime.date(year=2018, month=6, day=2)


@pytest.mark.django_db
def test_patch_credit_note_credited_invoice_outstanding_amount(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(500000),
        billed_amount=Decimal(500000),
        outstanding_amount=Decimal(500000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(500000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    credit_note = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CREDIT_NOTE,
        total_amount=Decimal(100000),
        billed_amount=Decimal(100000),
        recipient=contact,
        credited_invoice=invoice,
    )

    credit_note_row = land_use_agreement_invoice_row_factory(
        invoice=credit_note,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(502000.00)

    data = {
        "id": credit_note.id,
        "rows": [
            {
                "id": credit_note_row.id,
                "receivable_type": 1,
                "compensation_amount": 100000,
            }
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": credit_note.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.get(pk=invoice.id)

    assert invoice.outstanding_amount == Decimal(402000.00)


@pytest.mark.django_db
def test_patch_credit_note_dates_read_only(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(500000),
        billed_amount=Decimal(500000),
        outstanding_amount=Decimal(500000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(500000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    credit_note = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CREDIT_NOTE,
        total_amount=Decimal(100000),
        billed_amount=Decimal(100000),
        recipient=contact,
        credited_invoice=invoice,
        due_date=datetime.date(year=2018, month=1, day=1),
        notes="",
    )

    land_use_agreement_invoice_row_factory(
        invoice=credit_note,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(502000.00)

    data = {
        "id": credit_note.id,
        "due_date": datetime.date(year=2018, month=1, day=2),
        "notes": "Should change",
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": credit_note.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    credit_note = LandUseAgreementInvoice.objects.get(pk=credit_note.id)

    assert credit_note.notes == "Should change"
    assert credit_note.due_date == datetime.date(year=2018, month=1, day=1)


@pytest.mark.django_db
def test_patch_invoice_add_payment(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(200000),
        billed_amount=Decimal(200000),
        outstanding_amount=Decimal(200000),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "payments": [{"paid_amount": 100000, "paid_date": timezone.now().date()}],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.get(pk=invoice.id)

    assert invoice.billed_amount == Decimal(100000.00)
    assert invoice.outstanding_amount == Decimal(0.00)


@pytest.mark.django_db
def test_patch_invoice_cannot_add_payment_if_sent_to_sap(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(200000),
        billed_amount=Decimal(200000),
        outstanding_amount=Decimal(200000),
        recipient=contact,
        sent_to_sap_at=timezone.now(),
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(200000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "payments": [{"paid_amount": 100000, "paid_date": timezone.now().date()}],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice = LandUseAgreementInvoice.objects.get(pk=invoice.id)

    assert invoice.billed_amount == Decimal(201000.00)
    assert invoice.outstanding_amount == Decimal(201000.00)


@pytest.mark.django_db
def test_patch_invoice_existing_interest_row_success(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123456.78),
        billed_amount=Decimal(123456.78),
        outstanding_amount=Decimal(123456.78),
        recipient=contact,
    )

    invoice_row = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(100000),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row.id,
                "receivable_type": invoice_row.receivable_type_id,
                "compensation_amount": 100000,
            },
            {
                "receivable_type": 1,
                "compensation_amount": 150000,
                "increase_percentage": 5,
                "plan_lawfulness_date": datetime.date(2020, 5, 8),
                "receivable_type": 1,
                "sign_date": datetime.date(2020, 4, 8),
            },
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    invoice_row = LandUseAgreementInvoiceRow.objects.get(pk=invoice_row.id)

    assert invoice_row.amount == Decimal(100000.00)

    invoice = LandUseAgreementInvoice.objects.get(pk=response.data["id"])

    assert invoice.billed_amount == Decimal(251000.00)
    assert invoice.outstanding_amount == Decimal(251000.00)
    assert invoice.total_amount == Decimal(251000.00)


@pytest.mark.django_db
def test_patch_invoice_change_interest_row_fail(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123456.78),
        billed_amount=Decimal(123456.78),
        outstanding_amount=Decimal(123456.78),
        recipient=contact,
    )

    invoice_row = land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(123456.78),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),  # Rent
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row.id,
                "receivable_type": 2,
                "compensation_amount": 100000,
            }  # Interest
        ],
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_patch_invoice_new_interest_row_fail(
    admin_client,
    land_use_agreement_test_data,
    contact_factory,
    land_use_agreement_invoice_factory,
    land_use_agreement_invoice_row_factory,
):
    land_use_agreement = land_use_agreement_test_data

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = land_use_agreement_invoice_factory(
        land_use_agreement=land_use_agreement,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123456.78),
        billed_amount=Decimal(123456.78),
        outstanding_amount=Decimal(123456.78),
        recipient=contact,
    )

    land_use_agreement_invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        compensation_amount=Decimal(123456.78),
        increase_percentage=Decimal(5.0),
        plan_lawfulness_date=datetime.date(2020, 5, 8),
        sign_date=datetime.date(2020, 4, 8),  # Rent
    )

    data = {
        "id": invoice.id,
        "rows": [{"receivable_type": 2, "compensation_amount": 100000}],  # Interest
    }

    url = reverse("landuseagreementinvoice-detail", kwargs={"pk": invoice.id})
    response = admin_client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)
