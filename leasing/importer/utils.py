import re

from leasing.enums import ContactType
from leasing.importer.mappings import ASIAKASTYYPPI_MAP, MAA_MAP
from leasing.models import Contact

asiakas_cache = {}

PERSON_NAMES = [
]


def expand_lease_identifier(id):
    return {
        'id': id,
        'ALKUOSA': id[:id.index('-')],
        'TARKOITUS': id[0:2],
        'KUNTA': int(id[2:3]),
        'KAUPOSA': int(id[3:5]),
        'JUOKSU': int(id[id.index('-') + 1:])
    }


def expanded_id_to_query(expanded_id, where=True):
    if where:
        expanded_id['where_or_and'] = 'WHERE '
    else:
        expanded_id['where_or_and'] = 'AND '

    return """\n{where_or_and}TARKOITUS = '{TARKOITUS}'
AND KUNTA = {KUNTA}
AND KAUPOSA = {KAUPOSA}
AND JUOKSU = {JUOKSU}
""".format(**expanded_id)


def expanded_id_to_query_alku(expanded_id, where=True):
    if where:
        expanded_id['where_or_and'] = 'WHERE '
    else:
        expanded_id['where_or_and'] = 'AND '

    return """\n{where_or_and}ALKUOSA = '{ALKUOSA}'
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


def get_or_create_contact(data):  # NOQA
    if data['ASIAKAS']:
        if data['ASIAKAS'] in asiakas_cache:
            return asiakas_cache[data['ASIAKAS']]

        contact_type = ASIAKASTYYPPI_MAP[data['ASIAKASTYYPPI']]
        name = None
        first_name = None
        last_name = None

        if data['NIMI'].startswith('* '):
            data['NIMI'] = data['NIMI'][2:]

        data['NIMI'] = re.sub(r'\s+', ' ', data['NIMI'])

        if data['NIMI'].lower().endswith(' oy') or \
                'isännöitsijä' in data['NIMI'].lower() or \
                data['NIMI'].lower().endswith(' ry') or \
                data['NIMI'].lower().startswith('työ') or \
                'r.y.' in data['NIMI'].lower() or \
                ' oy ' in data['NIMI'].lower() or \
                'oyj' in data['NIMI'].lower() or \
                '/oy' in data['NIMI'].lower() or \
                'oy/' in data['NIMI'].lower() or \
                'skanska' in data['NIMI'].lower() or \
                'sosiaali' in data['NIMI'].lower() or \
                ' oy:n ' in data['NIMI'].lower() or \
                'as oy' in data['NIMI'].lower() or \
                'bo ab' in data['NIMI'].lower() or \
                'vvo-' in data['NIMI'].lower() or \
                'vvo ' in data['NIMI'].lower():
            contact_type = ContactType.BUSINESS

        if data['NIMI'] == 'ATT' or data['NIMI'].startswith('ATT/') or data['NIMI'].startswith('ATT ') or \
                data['NIMI'].endswith('/ATT'):
            contact_type = ContactType.UNIT

        if data['NIMI'] in PERSON_NAMES or 'kuolinp' in data['NIMI'].lower():
            contact_type = ContactType.PERSON

        if contact_type == ContactType.PERSON:
            name_parts = [p.strip() for p in data['NIMI'].split(' ') if p.strip()]

            if len(name_parts) == 1:
                last_name = name_parts[0]
            else:
                split_pos = 1
                if name_parts[0].lower() == 'af' or name_parts[0].lower() == 'von':
                    split_pos = 2

                last_name = ' '.join(name_parts[0:split_pos])
                first_name = ' '.join(name_parts[split_pos:])
        else:
            name = data['NIMI'].strip()

        if data['NIMI2'] and data['NIMI2'].strip():
            name += ' ' + data['NIMI2'].strip()

        language = None
        if data['KIELI'] == '1':
            language = 'fi'
        if data['KIELI'] == '2':
            language = 'sv'

        phone = []
        for i in range(1, 5):
            if data['PUHNO{}'.format(i)]:
                phone.append(data['PUHNO{}'.format(i)])

        postal_code = None
        if data['POSTINO']:
            postal_code = data['POSTINO'].strip()
            if postal_code == '.' or re.match(r'0+$', postal_code) or re.match(r'x+$', postal_code.lower()):
                postal_code = None

        (contact, contact_created) = Contact.objects.get_or_create(
            type=contact_type,
            first_name=first_name,
            last_name=last_name,
            name=name,
            address=data['OSOITE'],
            postal_code=postal_code,
            country=MAA_MAP[data['MAA']],
            business_id=data['LYTUNNUS'],
            # national_identification_number=data['HETU'],
            language=language,
            phone=', '.join(phone),
            note=data['KOMMENTTI'],
            email=data['SAHKOPOSTIOSOITE'],
            sap_customer_number=data['SAP_ASIAKASNUMERO'],
            partner_code=data['KUMPPANIKOODI'],
            electronic_billing_address=data['OVT_TUNNUS']
        )
    else:
        contact = get_unknown_contact()

    asiakas_cache[data['ASIAKAS']] = contact

    return contact
