from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from credit_integration.enums import CreditDecisionStatus
from credit_integration.models import CreditDecision, CreditDecisionLog
from leasing.enums import ContactType


def mock_return_company_json_data(business_id):
    return {
        "companyResponse": {
            "responseHeader": {
                "languageCode": "FI",
                "timeStamp": {"date": 1634590800000, "time": 23365000},
                "responseStatus": "0",
                "currencyCode": "EUR",
            },
            "identificationData": None,
            "companyBasics": None,
            "scoringData": [],
            "companyGroupReferences": None,
            "mergerData": None,
            "companyClassification": None,
            "registerData": None,
            "companyPaymentDefaultData": None,
            "personInCharge": None,
            "decisionMakers": None,
            "personInChargeSummary": [],
            "shareholderData": None,
            "paymentHistory": None,
            "errorMessage": None,
            "confirmationMessage": None,
            "authorisedSignaturesText": None,
            "authorisedSignaturesData": None,
            "mortgageData": None,
            "additionalNamesData": None,
            "newsRow": [],
            "paymentDefaultRefData": None,
            "additionalInformationRow": [],
            "companyHistoryRow": [],
            "lineOfBusinessLongRow": [],
            "listOfCompaniesRow": [],
            "decisionProposalData": {
                "usecode": "1",
                "model": {"code": "HEASYR", "name": "Yritysluottopäätökset"},
                "customerData": {
                    "customerDataRow": [],
                    "customerProductDataRow": [],
                    "name": "Solid Corporation Oy",
                    "businessId": business_id,
                    "personId": None,
                    "insertedInMonitoringText": None,
                    "customerKey": None,
                },
                "decisionProposal": {
                    "handler": None,
                    "inputRow": [],
                    "prosessingDate": 1634590800000,
                    "proposal": {
                        "code": "1",
                        "text": "Luottopäätös edellyttää lisäselvityksiä.",
                        "proposalCode": None,
                        "proposalText": None,
                        "factorRow": [
                            {
                                "code": "004",
                                "text": "Yritystä ei ole merkitty ennakkoperintärekisteriin.",
                            },
                            {
                                "code": "090",
                                "text": "Yritys on vanhempi kuin -1 kuukautta ja tilinpäätös puuttuu.",
                            },
                        ],
                    },
                },
            },
            "companyData": {
                "identificationData": {
                    "businessId": "30101929",
                    "name": "Solid Corporation Oy",
                    "domicileCode": None,
                    "domicile": None,
                    "companyLanguageCode": None,
                    "companyLanguageText": None,
                    "postalAddress": None,
                    "address": {
                        "street": "Kruunuvuorenkatu 3 E",
                        "zip": "00160",
                        "town": "Helsinki",
                    },
                    "contactInformation": {
                        "phone": "+358 44 7200965",
                        "fax": None,
                        "www": None,
                        "email": None,
                    },
                    "companyForm": "OY",
                    "companyFormText": "Osakeyhtiö",
                    "lineOfBusiness": {
                        "lineOfBusinessCode": "62010",
                        "lineOfBusinessText": "Ohjelmistojen suunnittelu ja valmistus",
                    },
                    "naceCode": None,
                    "naceText": None,
                },
                "startDate": None,
            },
            "populationInformation": None,
            "companyPaymentsAnalysis": None,
            "ratios": None,
            "tradeRegisterExtracts": None,
            "articlesOfAssociation": None,
            "authorizedSignature": None,
            "companysDomainNames": None,
            "queryHistoryInformation": None,
            "debtCollectionData": None,
            "bankruptcyIndicator": None,
            "beneficialOwner": None,
            "trustedCompanyData": None,
            "esgData": None,
            "valueReportData": None,
            "digitalActivityData": None,
            "growthIndicator": None,
            "officialRegisterBeneficialOwner": None,
            "authorisedSignaturesAbstract": None,
            "companyInGroup": [],
            "companyRadar": None,
            "leiData": None,
            "companyLoan": None,
            "shareholder2021Data": None,
            "authorizedSignature2021": None,
            "extract": None,
            "einvoiceData": None,
        },
        "groupResponse": None,
    }


def mock_return_consumer_json_data(identity_number):
    return {
        "consumerResponse": {
            "responseHeader": {
                "languageCode": "FI",
                "timeStamp": {"date": 1634590800000, "time": 40333000},
                "responseStatus": "0",
                "currencyCode": "EUR",
            },
            "personInformation": None,
            "profileData": None,
            "scoringBackgroundData": None,
            "scoringData": [],
            "decisionProposalData": {
                "usecode": "1",
                "model": {"code": "HEASKU", "name": "Kuluttajaluottopäätökset"},
                "customerData": {
                    "customerDataRow": [],
                    "customerProductDataRow": [],
                    "name": None,
                    "businessId": None,
                    "personId": identity_number,
                    "insertedInMonitoringText": None,
                    "customerKey": None,
                },
                "decisionProposal": {
                    "handler": None,
                    "inputRow": [],
                    "prosessingDate": 1634590800000,
                    "proposal": {
                        "code": "0",
                        "text": "Ehdotetaan hylättäväksi.",
                        "proposalCode": None,
                        "proposalText": None,
                        "factorRow": [
                            {
                                "code": "041",
                                "text": "Henkilöllä on maksuhäiriöitä 1, joka on vähintään 1 kpl.",
                            }
                        ],
                    },
                },
            },
            "populationInformation": None,
            "personIdentification": None,
            "soletrader": None,
            "paymentDefaultData": None,
            "creditInformationData": None,
            "noRegisteredMessage": None,
            "personInChargeSummary": None,
            "creditSummary": None,
            "assets": None,
            "taxInformation": None,
            "otherInformation": None,
            "errorMessage": None,
            "personInAssociationSummary": None,
            "officialRegisterBeneficialOwner": None,
        }
    }


@pytest.mark.django_db
def test_get_credit_decisions_endpoint(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    permission_names = [
        "view_creditdecision",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_get_credit_decisions_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()
    client.login(username=user.username, password=password)

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.get(
        reverse("credit_integration:get-credit-decisions"), data=data, format="json"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_business_id(
    client,
    user_factory,
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    business_id = "12345678"

    data = {"business_id": business_id}

    with patch(
        "credit_integration.views.request_company_decision",
        return_value=mock_return_company_json_data(business_id),
    ):
        response = client.post(
            reverse("credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert "id" in response.data[0]

    result_credit_decision_id = response.data[0]["id"]
    result_credit_decision = CreditDecision.objects.get(pk=result_credit_decision_id)
    assert result_credit_decision.status == CreditDecisionStatus.CONSIDERATION
    assert result_credit_decision.reasons.count() == 2
    assert result_credit_decision.business_id == business_id
    assert result_credit_decision.official_name
    assert result_credit_decision.address
    assert result_credit_decision.phone_number
    assert result_credit_decision.industry_code
    assert result_credit_decision.claimant == user
    assert result_credit_decision.original_data
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_identity_number(
    client,
    user_factory,
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    identity_number = "011213-1234"

    data = {"identity_number": identity_number}

    with patch(
        "credit_integration.views.request_consumer_decision",
        return_value=mock_return_consumer_json_data(identity_number),
    ):
        response = client.post(
            reverse("credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert "id" not in response.data[0]

    assert response.data[0]["status"] == CreditDecisionStatus.NO.value
    assert response.data[0]["claimant"]["first_name"] == "John"
    assert response.data[0]["claimant"]["last_name"] == "Doe"
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_with_person_contact(
    client, user_factory, contact_factory
):
    user_first_name = "John"
    user_last_name = "Doe"
    user = user_factory(first_name=user_first_name, last_name=user_last_name)
    password = "test"
    user.set_password(password)
    user.save()

    permission_names = [
        "send_creditdecision_inquiry",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.login(username=user.username, password=password)

    contact = contact_factory(
        first_name="Jane",
        last_name="Doe",
        type=ContactType.PERSON,
        national_identification_number="011213-1234",
    )
    data = {"customer_id": contact.id}

    with patch(
        "credit_integration.views.request_consumer_decision",
        return_value=mock_return_consumer_json_data(
            contact.national_identification_number
        ),
    ):
        response = client.post(
            reverse("credit_integration:send-credit-decision-inquiry"),
            data=data,
            format="json",
        )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert "id" not in response.data[0]

    assert response.data[0]["status"] == CreditDecisionStatus.NO.value
    assert response.data[0]["claimant"]["first_name"] == "John"
    assert response.data[0]["claimant"]["last_name"] == "Doe"
    assert CreditDecisionLog.objects.count() == 1


@pytest.mark.django_db
def test_send_credit_decision_inquiry_endpoint_without_access_right(
    client,
    user_factory,
    credit_decision_reason_factory,
    business_credit_decision_factory,
):
    user = user_factory()
    password = "test"
    user.set_password(password)
    user.save()

    client.login(username=user.username, password=password)

    business_id = "12345678"
    business_credit_decision_factory(
        business_id=business_id,
        reasons=(credit_decision_reason_factory(), credit_decision_reason_factory()),
    )

    data = {"business_id": business_id}
    response = client.post(
        reverse("credit_integration:send-credit-decision-inquiry"),
        data=data,
        format="json",
    )

    assert response.status_code == 403
