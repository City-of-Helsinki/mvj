import json
from pathlib import Path

import factory
import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from faker import Faker

from forms.models import Answer
from plotsearch.models.plot_search import AreaSearch
from utils.email import EmailMessageInput

fake = Faker("fi_FI")


@pytest.fixture
def basic_template_form_with_required_fields(basic_template_form):
    sections = basic_template_form.sections.all()
    for section in sections:
        if section.identifier != "person-information":
            continue
        for field in section.fields.all():
            field.required = True
            field.save()

    return basic_template_form


@pytest.fixture
def basic_form_data():
    return {
        "name": fake.name(),
        "description": fake.sentence(),
        "is_template": False,
        "title": fake.sentence(),
    }


@pytest.fixture
def basic_form(basic_template_form):
    basic_template_form.is_template = False
    basic_template_form.save()
    return basic_template_form


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Loads all the database fixtures in the plotsearch/fixtures and leasing/fixtures folder"""
    fixture_path = Path(__file__).parents[1].parent / "plotsearch/fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)

    fixture_path = Path(__file__).parents[1].parent / "leasing/fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)


class AnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Answer


@pytest.fixture
def answer_with_email(
    admin_client,
    area_search_intended_use_factory,
    user_factory,
    area_search_form,
):
    user = user_factory(username=fake.name())
    intended_use = area_search_intended_use_factory(
        name="Urheilu ja liikunta", name_fi="Urheilu ja liikunta"
    )

    area_search_payload = {
        "area_search_attachments": [],
        "geometry": (
            '{"coordinates":[[[[24.927311,60.188275],[24.928843,60.188204],[24.929369,60.186652],'
            "[24.928722,60.185772],[24.926181,60.185546],[24.924826,60.187116],[24.924482,60.187717],"
            "[24.92531,60.188472],[24.926571,60.188589],[24.927311,60.188275]]]],"
            '"type":"MultiPolygon"}'
        ),
        "start_date": "2023-11-06T22:00:00.000Z",
        "description_area": "Olympic stadium area",
        "description_intended_use": "Want to hold Helsinki Olympics 2028 here",
        "attachments": [],
        "intended_use": intended_use.id,
        "end_date": "2023-11-29T22:00:00.000Z",
    }

    url = reverse("v1:pub_area_search-list")
    response = admin_client.post(url, data=area_search_payload)
    area_search = AreaSearch.objects.get(id=response.data["id"])

    def _get_company_applicants(count=1):
        if count > 10:
            count = 10
        company_applicants = []
        emails = iter([f"user{i}@example.com" for i in range(1, 11)])
        company_ids = iter(
            [
                "3154053-6",
                "8527616-0",
                "7062724-7",
                "8253184-0",
                "4388112-7",
                "6833006-5",
                "6376250-4",
                "5281453-2",
                "8008574-4",
                "1274040-1",
                "1150642-9",
                "1561624-6",
                "4263272-7",
                "7720431-9",
                "4416074-3",
            ]
        )
        company_names = iter(
            [
                "Sepposen Betoni Oy",
                "Hattulan kultakaivos Oy",
                "Kuusamon bajamajat Ky",
                "Avaruusolioiden ystävät ry",
                "Wirren Wirkkuu Tmi",
                "Helsingin Olympialaiset 2028 Oy",
                "Oulun alakaupunki ry",
                "Heikin hiekka Ky",
                "George's Barbershop Oy",
                "Kytky-Kauppa Oy",
            ]
        )
        for _ in range(count):
            email = next(emails)
            company_id = next(company_ids)
            company_applicants.append(
                {
                    "sections": {
                        "yrityksen-tiedot": {
                            "sections": {
                                "laskutustiedot": {
                                    "sections": {
                                        "laskutusviite": {
                                            "sections": {},
                                            "fields": {
                                                "verkkolaskutusosoite": {
                                                    "value": "1122334455",
                                                    "extraValue": "",
                                                },
                                                "laskutusviite": {
                                                    "value": "99887766",
                                                    "extraValue": "",
                                                },
                                            },
                                        }
                                    },
                                    "fields": {
                                        "kieli": {"value": "suomi", "extraValue": ""},
                                        "puhelinnumero": {
                                            "value": "+123456789",
                                            "extraValue": "",
                                        },
                                        "sahkoposti": {
                                            "value": email,
                                            "extraValue": "",
                                        },
                                        "katuosoite": {
                                            "value": "Paavo Nurmen tie 2",
                                            "extraValue": "",
                                        },
                                        "maa": {"value": "", "extraValue": ""},
                                        "postitoimipaikka": {
                                            "value": "Helsinki",
                                            "extraValue": "",
                                        },
                                        "postinumero": {
                                            "value": "00250",
                                            "extraValue": "",
                                        },
                                    },
                                }
                            },
                            "fields": {
                                "yrityksen-nimi": {
                                    "value": next(company_names),
                                    "extraValue": "",
                                },
                                "y-tunnus": {"value": company_id, "extraValue": ""},
                                "kieli": {"value": "suomi", "extraValue": ""},
                                "puhelinnumero": {
                                    "value": "+123456789",
                                    "extraValue": "",
                                },
                                "sahkoposti": {"value": email, "extraValue": ""},
                                "katuosoite": {
                                    "value": "Paavo Nurmen tie 2",
                                    "extraValue": "",
                                },
                                "postinumero": {"value": "00250", "extraValue": ""},
                                "postitoimipaikka": {
                                    "value": "Helsinki",
                                    "extraValue": "",
                                },
                                "maa": {"value": "", "extraValue": ""},
                                "hallintaosuus": {
                                    "value": f"1 / {count}",
                                    "extraValue": "",
                                },
                            },
                        }
                    },
                    "fields": {"hakija": {"value": "1", "extraValue": ""}},
                    "metadata": {"applicantType": "company", "identifier": company_id},
                }
            )

        return company_applicants

    answer_entries = {
        "sections": {
            "hakijan-tiedot": _get_company_applicants(count=3),
            "paatoksen-toimitus": {
                "sections": {},
                "fields": {
                    "sahkoisesti-ilmoittamaani-sahkopostiosoitteeseen": {
                        "value": True,
                        "extraValue": "",
                    },
                    "postitse-ilmoittamaani-postiosoitteeseen": {
                        "value": True,
                        "extraValue": "",
                    },
                },
            },
        }
    }

    answer_payload = {
        "form": area_search_form.id,
        "area_search": area_search.id,
        "user": user.id,
        "entries": json.dumps(answer_entries),
        "ready": True,
    }

    url = reverse("v1:pub_answer-list")
    response = admin_client.post(url, data=answer_payload)

    return {"answer": response.data, "area_search": area_search}


@pytest.fixture
def answer_email_message():
    email: EmailMessageInput = {
        "subject": "Test email",
        "body": "This is a test email",
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "to": ["test@example.com"],
        "attachments": [],
    }
    return email
