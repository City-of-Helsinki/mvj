[![codecov](https://codecov.io/gh/City-of-Helsinki/mvj/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/mvj)

# mvj

City of Helsinki ground rent system

## Development with Docker

1. Run `docker-compose up`

2. Run migrations if needed:

   - `docker exec mvj python manage.py migrate`

3. Create superuser if needed:
   - `docker exec -it mvj python manage.py createsuperuser`

The project is now running at [localhost:8000](http://localhost:8000)

### Settings for development environment

```bash
cd mvj
# copy sanitized.sql to root
docker-compose exec django bash
psql -h postgres -U mvj -d mvj < sanitized.sql
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py createsuperuser #(github sähköposti)
```

- Luo leasing/management/commands/copy_groups.py:

```python
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
GROUPS = {
    1: "Selailija test",
    2: "Valmistelija test",
    3: "Sopimusvalmistelija test",
    4: "Syöttäjä test",
    5: "Perintälakimies test",
    6: "Laskuttaja test",
    7: "Pääkäyttäjä test",
}
class Command(BaseCommand):
    def handle(self, *args, **options):
        for group in Group.objects.filter(id__in=GROUPS.keys()):
            (new_group, created) = Group.objects.get_or_create(
id=group.id + 10, defaults={"name": GROUPS[group.id]} )
            new_group.permissions.set(group.permissions.all())
```

```bash
docker-compose exec django python manage.py copy_groups
```

- Lisää luodulle käyttäjälle "Pääkäyttäjä test"-ryhmä Django adminissa

### Connecting to Tunnistamo

If you have a Tunnistamo and an mvj-ui instance running with docker in separate docker-compose
environments, you can set up a network to sync mvj, mvj-ui and tunnistamo together.

1.  Add network definition to tunnistamo's `docker-compose`:

        version: '3'
        services:
            postgres:
                ...
                networks:
                    - net

            django:
                ...
                networks:
                    - net

        networks:
            net:
                driver: bridge

2.  Connect mvj to tunnistamo's network, by adding this to mvj's and mvj-ui's `docker-compose`:

        networks:
            default:
                external:
                    name: tunnistamo_net

    The name `tunnistamo_net` comes from the name of the folder, where tunnistamo lives
    combined with the name of the network. Change those according to your setup, if needed.

3.  Now you can access tunnistamo from other docker containers with `tunnistamo-backend`,
    i.e. Tunnistamo's `django` container's name. Connect mvj's OIDC logic to that like so:

            OIDC_API_TOKEN_AUTH = {
                ...
                'ISSUER': 'http://tunnistamo-backend:8001/openid',
                ...
            }

4.  Add `tunnistamo-backend` to your computer's localhost aliases. To do this on UNIX-like systems open
    `/etc/hosts` and add it:

            127.0.0.1    localhost tunnistamo-backend

    This way callbacks to `tunnistamo-backend` URL will work locally.

5.  Configure OIDC settings in Tunnistamo's admin panel. Might require help from other devs.

6.  Configure some social auth application to allow requests from your local tunnistamo by using this
    URL in the settings `http://tunnistamo-backend`

### Settings for Tunnistamo

```bash
docker-compose exec django python manage.py createsuperuser
```
Django adminissa:
* Lisää uusi Login Method: yletunnus
* OpenID Connect Provider / Clients / Lisää client:
  * Name: mvj
  * Client Type: public
  * Response types: id_token token (Implicit Flow)
  * Redirect URIs: http://localhost:3000/callback <uusi rivi> http://localhost:3000/silent_renew.html
  * Client ID: https://api.hel.fi/auth/mvj
  * Site type: Development
  * Login methods: GitHub
* Oidc_Apis / APIs / Lisää API:
  * Domain: https://api.hel.fi/auth
  * Nimi: mvj
  * Required scopes: Sähköposti, Profile, Address, AD Groups
  * OIDC client: mvj
* Oidc_Apis / API scopes / Lisää API scope:
  * API: https://api.hel.fi/auth/mvj
  * Nimi: mvj
  * Description: lue ja modifioi
  * Allowed applications: mvj

* Kopioi docker-compose.env.template -> docker-compose.env
* Lisää docker-compose.env.yaml SOCIAL_AUTH_GITHUB_KEY ja SOCIAL_AUTH_GITHUB_SECRET Githubista

## Development without Docker

### Install required system packages

#### PostgreSQL and PostGIS

Install PostgreSQL and PostGIS.

    # Ubuntu 16.04
    sudo apt-get install python3-dev libpq-dev postgresql postgis

#### GeoDjango extra packages

    # Ubuntu 16.04
    sudo apt-get install binutils libproj-dev gdal-bin

### Creating a Python virtualenv

Create a Python 3.x virtualenv either using the [`venv`](https://docs.python.org/3/library/venv.html) tool or using
the great [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) toolset. Assuming the latter,
once installed, simply do:

    mkvirtualenv -p /usr/bin/python3 mvj

The virtualenv will automatically activate. To activate it in the future, just do:

    workon mvj

### Creating Python requirements files

- Run `pip install pip-tools`
- Run `pip-compile requirements.in`
- Run `pip-compile requirements-dev.in`

### Updating Python requirements files

- Run `pip-compile --upgrade requirements.in`
- Run `pip-compile --upgrade requirements-dev.in`

### Installing Python requirements

- Run `pip install -r requirements.txt`
- For development also run `pip install -r requirements-dev.txt`

### Database

To setup a database compatible with the default database settings:

Create user and database

    sudo -u postgres createuser -P -R -S mvj  # use password `mvj`
    sudo -u postgres createdb -O mvj mvj

Enable PostGIS

    sudo -u postgres psql -d "mvj" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Allow the mvj user to create databases when running tests

    sudo -u postgres psql -d "mvj" -c "ALTER USER mvj CREATEDB;"

Tests also require that PostGIS extension is installed on the test database. This can be achieved the easiest by
adding PostGIS extension to the default template which is then used when the test databases are created:

    sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"

### Django configuration

Environment variables are used to customize configuration in `mvj/settings.py`. If you wish to override any
settings, you can place them in a local `.env` file which will automatically be sourced when Django imports
the settings file.

Alternatively you can create a `local_settings.py` which is executed at the end of the `mvj/settings.py` in the
same context so that the variables defined in the settings are available.

#### Notice!

The "idc_attachments"-folder under the media root must be excluded when serving media files. The files are
protected by permission checks on a different URL.

### Running development environment

- Enable debug `echo 'DEBUG=True' >> .env`
- Run `python manage.py migrate`
- Run `python manage.py loaddata */fixtures/*.json`
- Run `python manage.py runserver 0.0.0.0:8000`

## Running tests

- Run `pytest`

## Update translation files

- Run `python manage.py app_makemessages`

## Management commands

There are multiple management commands that are required to run. Either when first installing the software or regularly.

### Install time commands

#### `set_report_permissions`

Sets permitted groups for each report type.

#### `set_group_model_permissions`

Sets the default model specific permissions (view, add, change, delete) to the pre-defined groups for the leasing models.

#### `set_group_field_permissions`

Sets field specific permissions (view, change) to the pre-defined groups.

#### `set_ad_group_mappings`

Sets the default mappings for AD groups to user groups.

### Regularly run commands

#### `create_invoices`

Creates invoices for rents that are due in the next month.

_Should be run on the first day of every month_

#### `send_invoices_to_laske`

Sends unsent invoices to Laske SAP for invoicing.

_Should be run every night_

#### `import_index`

Imports index from stat.fi.

_Should be run monthly after stat.fi update day_

#### `import_interest_rate`

Imports reference interest rates from the Bank of Finland.

_Should be run after the Bank of Finland releases new rates_

#### `index_rent_equalization`

Creates credit notes or invoices if index number has changed after the invoices are sent.

_Should be run once a year after the previous years index has been released_

#### `import_leasehold_transfers`

Imports leasehold transfers from National Land Survey of Finland (Maanmittauslaitos).

_Should be run every week_

### Development commands

No need to run.

#### `attach_areas`

#### `compare_rent_amounts`

#### `mvj_import`

#### `set_contact_cities_from_postcodes`
