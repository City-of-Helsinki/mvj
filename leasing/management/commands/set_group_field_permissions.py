import collections

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

# 1 Selailija
# 2 Valmistelija
# 3 Sopimusvalmistelija
# 4 Syöttäjä
# 5 Perintälakimies
# 6 Laskuttaja
# 7 Pääkäyttäjä

DEFAULT_FIELD_PERMS = {
    "areanote": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "decision": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "condition": {
        1: "view",
        2: "change",
        3: "change",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "rent": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "rentduedate": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "change",
        7: "change",
    },
    "fixedinitialyearrent": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "contractrent": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "rentadjustment": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "leasebasisofrent": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "basisofrent": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "basisofrentrate": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "basisofrentdecision": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "comment": {
        1: None,
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "commenttopic": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "view",
        7: "change",
    },
    "contact": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "change",
        7: "change",
    },
    "contract": {
        1: "view",
        2: "view",
        3: "change",
        4: "view",
        5: "view",
        6: "view",
        7: "change",
    },
    "contractchange": {
        1: "view",
        2: "view",
        3: "change",
        4: "view",
        5: "view",
        6: "view",
        7: "change",
    },
    "collateral": {
        1: "view",
        2: "view",
        3: "change",
        4: "view",
        5: "view",
        6: "change",
        7: "change",
    },
    "collectionletter": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "change",
        6: "view",
        7: "change",
    },
    "collectionnote": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "change",
        6: "view",
        7: "change",
    },
    "collectioncourtdecision": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "change",
        6: "view",
        7: "change",
    },
    "lease": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "infilldevelopmentcompensation": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "infilldevelopmentcompensationlease": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "infilldevelopmentcompensationdecision": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "infilldevelopmentcompensationintendeduse": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "infilldevelopmentcompensationattachment": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "inspection": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "invoice": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "change",
        7: "change",
    },
    "invoicerow": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "change",
        7: "change",
    },
    "invoicenote": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "change",
        7: "change",
    },
    "invoicepayment": {
        1: None,
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "change",
        7: "change",
    },
    "leasearea": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "leaseareaaddress": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "leaseareaattachment": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "leaseholdtransfer": {
        1: "view",
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "view",
        7: "view",
    },
    "leaseholdtransferparty": {
        1: "view",
        2: "view",
        3: "view",
        4: "view",
        5: "view",
        6: "view",
        7: "view",
    },
    "constructabilitydescription": {
        1: "view",
        2: "change",
        3: "view",
        4: "change",
        5: "change",
        6: "view",
        7: "change",
    },
    "plot": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "planunit": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "tenant": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "view",
        7: "change",
    },
    "tenantcontact": {
        1: "view",
        2: "view",
        3: "view",
        4: "change",
        5: "view",
        6: "change",
        7: "change",
    },
}

CUSTOM_FIELD_PERMS = {
    "lease": {
        "tenants": {
            2: "view",
            5: "view",
            6: "change",
        },
        "rents": {
            2: "view",
            6: "change",
        },
        "decisions": {
            3: "change",
        },
        "contracts": {
            3: "change",
            6: "change",
        },
        "invoice_notes": {
            2: "view",
            4: "view",
            5: "view",
            6: "change",
        },
        "is_invoicing_enabled": {
            2: "view",
            4: "view",
            5: "view",
            6: "change",
        },
        "is_rent_info_complete": {
            2: "view",
            5: "view",
        },
    },
    "contact": {
        "national_identification_number": {
            1: None,
            2: None,
            3: None,
            4: "change",
            5: "view",
            6: "change",
            7: "change",
        },
        "phone": {
            2: "change",
            5: "change",
        },
        "email": {
            2: "change",
            5: "change",
        },
    },
    "condition": {
        "id": {
            2: "view",
            3: "view",
            5: "view",
        },
        "type": {
            2: "view",
            3: "view",
            5: "view",
        }
    },
    "contract": {
        "ktj_link": {
            2: "change",
            4: "change",
            5: "change",
        },
        "collaterals": {
            6: "change",
        },
    },
    "decision": {
        "conditions": {
            2: "change",
            3: "change",
            5: "change",
        },
    },
    "rent": {
        "due_dates_type": {
            6: "change",
        },
        "due_dates_per_year": {
            6: "change",
        },
        "due_dates": {
            6: "change",
        },
    },
    "tenant": {
        "reference": {
            6: "change",
        },
        "tenantcontact_set": {
            6: "change",
        }
    },
    "leasearea": {
        "plots": {
            2: "view",
            5: "view",
        },
        "plan_units": {
            2: "view",
            5: "view",
        },
        "archived_at": {
            2: "view",
            5: "view",
        },
        "archived_note": {
            2: "view",
            5: "view",
        },
        "archived_decision": {
            2: "view",
            5: "view",
        },
    },
    "leaseholdtransferparty": {
        "national_identification_number": {
            1: None,
            2: None,
            3: None,
        },
    },
}


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v

    return d


class Command(BaseCommand):
    help = 'Sets predefined field permissions for the predefined MVJ groups'

    def handle(self, *args, **options):  # NOQA
        if not apps.is_installed("field_permissions"):
            raise CommandError('App "field_permissions" must be installed to use this command.')

        from field_permissions.registry import field_permissions

        groups = {group.id: group for group in Group.objects.all()}
        permissions = {perm.codename: perm for perm in Permission.objects.all()}

        group_permissions = []
        all_field_permissions = []

        for model in field_permissions.get_models():
            model_name = model._meta.model_name

            # Find all the fields that the field permissions registry knows about
            perms = field_permissions.get_field_permissions_for_model(model)

            field_perms = {}
            for (codename, name) in sorted(perms):
                try:
                    all_field_permissions.append(permissions[codename])
                except KeyError:
                    raise CommandError('"{}" field permission is missing. Please run migrate to create '
                                       'the missing permissions.'.format(codename))

                if codename.startswith('change_'):
                    continue

                field_name = codename.replace('view_{}_'.format(model_name), '')

                # Set field permissions to their default value
                if model_name in DEFAULT_FIELD_PERMS:
                    field_perms[field_name] = dict(DEFAULT_FIELD_PERMS[model_name])

            # Customize field permissions for this model
            if model_name in CUSTOM_FIELD_PERMS:
                update(field_perms, CUSTOM_FIELD_PERMS[model_name])

            # Generate Group permissions for all of the fields and groups
            for field_name, group_perms in field_perms.items():
                for group_id, permission_type in group_perms.items():
                    if not permission_type:
                        continue

                    permission_name = '{}_{}_{}'.format(permission_type, model_name, field_name)

                    group_permissions.append(
                        Group.permissions.through(group=groups[group_id], permission=permissions[permission_name])
                    )

        # Delete existing field permissions from the pre-defined groups
        mvj_groups = [grp for grp in groups.values() if grp.id in range(1, 8)]
        Group.permissions.through.objects.filter(group__in=mvj_groups, permission__in=all_field_permissions).delete()

        # Save the desired field permissions for the groups
        Group.permissions.through.objects.bulk_create(group_permissions)
        for group_permission in group_permissions:
            self.stdout.write('Added field permission "{}" for group "{}"'.format(
                group_permission.permission.codename, group_permission.group.name))
