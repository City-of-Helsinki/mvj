# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
from random import choice
from string import digits

from faker import Faker

fake = Faker("fi_FI")

# Original value will be passed to the sanitization function as a paremeter,
# even if it is not used when generating the sanitized replacement value.


def sanitize_address(value):
    address = fake.address()
    address_without_linebreak = address.replace("\n", ", ")
    return address_without_linebreak


def sanitize_address_if_exist(value):
    if value:
        return sanitize_address(value)
    elif value == "":
        return ""


def sanitize_street_address(value):
    return fake.street_address()


def sanitize_street_address_if_exist(value):
    if value:
        return sanitize_street_address(value)
    elif value == "":
        return ""


def sanitize_business_id(value):
    return fake.pystr_format(string_format="#######-#", letters="0123456789")


def sanitize_business_id_if_exist(value):
    if value:
        return sanitize_business_id(value)
    elif value == "":
        return ""


def sanitize_city(value):
    return fake.city()


def sanitize_city_if_exist(value):
    if value:
        return sanitize_city(value)
    elif value == "":
        return ""


def sanitize_company(value):
    return fake.company()


def sanitize_company_if_exist(value):
    if value:
        return sanitize_company(value)
    elif value == "":
        return ""


def sanitize_email(value):
    return fake.email()


def sanitize_email_if_exist(value):
    if value:
        return sanitize_email(value)
    elif value == "":
        return ""


def sanitize_first_name(value):
    return fake.first_name()


def sanitize_first_name_if_exist(value):
    if value:
        return sanitize_first_name(value)
    elif value == "":
        return ""


def sanitize_generate_random_numbers():
    return "".join([choice(digits) for _ in range(random.randint(1, 10))])


def sanitize_generate_random_numbers_if_exist(value):
    if value:
        return sanitize_generate_random_numbers()
    elif value == "":
        return ""


def sanitize_last_name(value):
    return fake.last_name()


def sanitize_last_name_if_exist(value):
    if value:
        return sanitize_last_name(value)
    elif value == "":
        return ""


def sanitize_national_identification_number(value):
    """
    Generate a mock of a Finnish national identification number (henkilötunnus).
    To avoid collisions, we're using years larger than 2050.
    """
    day = random.randint(1, 28)  # Avoid edge cases with 29-31
    month = random.randint(1, 12)

    century_marker = "A"  # For years 2000-2099
    year = random.randint(50, 99)

    date_part = f"{day:02d}{month:02d}{year:02d}"
    individual_number = random.randint(1, 899)
    number_without_control_char = f"{date_part}{century_marker}{individual_number:03d}"

    control_number = int(date_part + f"{individual_number:03d}") % 31
    control_chars = "0123456789ABCDEFHJKLMNPRSTUVWXY"
    control_char = control_chars[control_number]

    return number_without_control_char + control_char


def sanitize_national_identification_number_if_exist(value):
    if value:
        return sanitize_national_identification_number(value)
    elif value == "":
        return ""


def sanitize_name(value):
    return fake.name()


def sanitize_paragraph(value):
    return fake.paragraph()


def sanitize_paragraph_if_exist(value):
    if value:
        return sanitize_paragraph(value)
    elif value == "":
        return ""


def sanitize_phone_number(value):
    return fake.phone_number()


def sanitize_phone_number_if_exist(value):
    if value:
        return sanitize_phone_number(value)
    elif value == "":
        return ""


def sanitize_postcode(value):
    return fake.postcode()


def sanitize_postcode_if_exist(value):
    if value:
        return sanitize_postcode(value)
    elif value == "":
        return ""


def sanitize_url(value):
    return fake.url()
