# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
from random import choice
from string import digits

from faker import Faker

fake = Faker("fi_FI")


def sanitize_address(value):
    return fake.address()


def sanitize_address_if_exist(value):
    if value:
        return sanitize_address(value)


def sanitize_business_id(value):
    return fake.pystr_format(string_format="#######-#", letters="0123456789")


def sanitize_business_id_if_exist(value):
    if value:
        return sanitize_business_id(value)


def sanitize_city(value):
    return fake.city()


def sanitize_city_if_exist(value):
    if value:
        return sanitize_city(value)


def sanitize_company(value):
    return fake.company()


def sanitize_company_if_exist(value):
    if value:
        return sanitize_company(value)


def sanitize_email(value):
    return fake.email()


def sanitize_email_if_exist(value):
    if value:
        return sanitize_email(value)


def sanitize_first_name(value):
    return fake.first_name()


def sanitize_first_name_if_exist(value):
    if value:
        return sanitize_first_name(value)


def sanitize_generate_random_numbers(value):
    return "".join([choice(digits) for i in range(random.randint(0, 10))])


def sanitize_generate_random_numbers_if_exist(value):
    if value:
        return sanitize_generate_random_numbers(value)


def sanitize_last_name(value):
    return fake.first_name()


def sanitize_last_name_if_exist(value):
    if value:
        return sanitize_last_name(value)


def sanitize_national_identification_number(value):
    return fake.pystr_format(string_format="######-####", letters="0123456789")


def sanitize_national_identification_number_if_exist(value):
    if value:
        return sanitize_national_identification_number(value)


def sanitize_name(value):
    return fake.name()


def sanitize_paragraph(value):
    return fake.paragraph()


def sanitize_paragraph_if_exist(value):
    if value:
        return sanitize_paragraph(value)


def sanitize_phone_number(value):
    return fake.phone_number()


def sanitize_phone_number_if_exist(value):
    if value:
        return sanitize_phone_number(value)


def sanitize_postcode(value):
    return fake.postcode()


def sanitize_postcode_if_exist(value):
    if value:
        return sanitize_postcode(value)


def sanitize_url(value):
    return fake.url()
