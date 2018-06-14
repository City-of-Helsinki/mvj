import re

from leasing.enums import ContactType
from leasing.importer.mappings import ASIAKASTYYPPI_MAP
from leasing.models import Contact

asiakas_cache = {}


def expand_lease_identifier(id):
    return {
        'id': id,
        'ALKUOSA': id[:id.index('-')],
        'TARKOITUS': id[0:2],
        'KUNTA': int(id[2:3]),
        'KAUPOSA': int(id[3:5]),
        'JUOKSU': int(id[id.index('-') + 1:])
    }


def expanded_id_to_query(expanded_id):
    return """
AND TARKOITUS = '{TARKOITUS}'
AND KUNTA = {KUNTA}
AND KAUPOSA = {KAUPOSA}
AND JUOKSU = {JUOKSU}
""".format(**expanded_id)


def expanded_id_to_query_alku(expanded_id):
    return """
AND ALKUOSA = '{ALKUOSA}'
AND JUOKSU = {JUOKSU}
""".format(**expanded_id)


def rows_to_dict_list(cursor):
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]


def get_real_property_identifier(data):
    identifier_parts = [data['KUNTATUNNUS'], data['KAUPOSATUNNUS'], data['KORTTELI'], data['TONTTI'], ]

    for i, identifier_part in enumerate(identifier_parts):
        if re.fullmatch(r'0*', identifier_part):
            identifier_parts[i] = '0'
        else:
            identifier_parts[i] = identifier_part.lstrip('0')

    identifier = '-'.join(identifier_parts)

    if data['MVJ_PALSTA'] and data['MVJ_PALSTA'] != '000':
        identifier += '-P{}'.format(data['MVJ_PALSTA'].lstrip('0'))

    return identifier


def get_unknown_contact():
    (contact, contact_created) = Contact.objects.get_or_create(
        type=ContactType.OTHER, first_name='Unknown', last_name='Unknown', name='Unknown')

    return contact


def get_or_create_contact(data):
    if data['ASIAKAS']:
        if data['ASIAKAS'] in asiakas_cache:
            return asiakas_cache[data['ASIAKAS']]

        contact_type = ASIAKASTYYPPI_MAP[data['ASIAKASTYYPPI']]
        name = None
        first_name = None
        last_name = None

        if contact_type == ContactType.PERSON:
            last_name = data['NIMI'].split(' ', 1)[0]
            try:
                first_name = data['NIMI'].split(' ', 1)[1]
            except IndexError:
                pass
        else:
            name = data['NIMI']

        (contact, contact_created) = Contact.objects.get_or_create(type=contact_type, first_name=first_name,
                                                                   last_name=last_name, name=name,
                                                                   address=data['OSOITE'],
                                                                   postal_code=data['POSTINO'],
                                                                   business_id=data['LYTUNNUS'])
    else:
        contact = get_unknown_contact()

    asiakas_cache[data['ASIAKAS']] = contact

    return contact
