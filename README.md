[![codecov](https://codecov.io/gh/City-of-Helsinki/mvj/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/mvj)

# mvj

City of Helsinki land lease system


## Development with development container (devcontainer)

Code editors (e.g. VSCode, Pycharm) that support devcontainer spec should be able to build and run your development environment from `.devcontainer`, either locally or remotely.
See: [https://containers.dev/](https://containers.dev/)

The devcontainer setup will build and run containers for the database and django.
Integrated to the editor you gain access to the shell within the django container, running code with debugger or run tests in debugging mode should work without much hassle.


## Development with Docker

If using Apple M1/M2 chip (or equivalent), you need to add `platform: linux/amd64` to `django` service in `docker-compose.yml` file.

1. Run `docker-compose up`

2. Run migrations if needed (if you have sanitized.sql file then skip 2. and 3. Continue to "Settings for development environment"):

   - `docker exec mvj python manage.py migrate`

3. Create superuser if needed:
   - `docker exec -it mvj python manage.py createsuperuser`

The project is now running at [localhost:8000](http://localhost:8000).

Known issues:
- runserver_plus not found/not working: replace `command: python manage.py runserver_plus 0:8000` with `command: python manage.py runserver 0:8000` command in `docker-compose.yml`.

### Settings for development environment

```bash
cd mvj
# copy sanitized.sql to root
docker-compose exec django bash
psql -h postgres -U mvj -d mvj < sanitized.sql
docker-compose exec django python manage.py migrate
docker-compose exec django python manage.py createsuperuser #(github email)
```

- Create TEST groups by:
```bash
python manage.py copy_groups_and_service_unit_mappings
```

- Add "TEST Pääkäyttäjä" -group to created user at Django admin.


## Development without Docker

### Install required system packages

#### PostgreSQL and PostGIS

Install PostgreSQL and PostGIS.

    # Ubuntu
    sudo apt-get install python3-dev libpq-dev postgresql postgis

#### GeoDjango extra packages

    # Ubuntu
    sudo apt-get install binutils libproj-dev gdal-bin

### Creating a Python virtualenv

Create a Python 3 virtualenv either using the [`venv`](https://docs.python.org/3/library/venv.html) tool.

    python3 -m venv /path/to/venv

Activate virtualenv

    python3 venv/bin/activate

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

- Run `python manage.py app_makemessages --locale fi`
- Run `python manage.py app_makemessages --locale sv`
- Run `python manage.py compilemessages`

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

#### `set_service_unit_group_mappings`

Sets the default user group to Service unit mappings. Creates a group for the Service unit if a group doesn't exist
already. The `service_unit.json` fixture has to be loaded into the database before running this command.

#### `set_default_lessors`

Adds the default lessor contacts for all the Service units. The `service_unit.json` fixture has to be loaded into the
database before running this command.

#### `set_receivable_types_for_service_units`

Adds the default receivable types for all the Service units. The `service_unit.json` should be loaded into the
database before running this command.

#### `create_filescanstatus_for_missing_files`

Creates FileScanStatus objects for all uploaded files that require a virus scan
in order to be downloaded.

Only needs to be run once per environment if there are historical uploaded files
that were uploaded before virus scanning was added to the system. Afterwards,
run `enqueue_scan_for_pending`.

#### `enqueue_scan_for_pending`

Enqueues an asynchronous virus scan for all FileScanStatus objects whose result
is `Pending`, or `Error`. After the async jobs complete, infected files have been deleted,
and safe files can be downloaded.

Only needs to be run if there are FileScanStatus objects that have not yet been
successfully scanned by the file scanning service.  This means that the command
also retries all filescans that resulted in an error previously. Before this
one, run `create_filescanstatus_for_missing_files`.

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

#### `generate_export_report_lease_statistic`

Generates Lease statistics report for Export API.

Can be generated in desired intervals, how often the report should need to be updated. For now daily.

### Development commands

No need to run.

#### `attach_areas`

#### `compare_rent_amounts`

#### `mvj_import`

#### `set_contact_cities_from_postcodes`

## Other useful information

### Resend Invoices

You can resend the failed invoices in [Django admin Invoices](https://mvj.dev.hel.ninja/admin/leasing/invoice/) view by selecting the invoices and chosing Resend invoice action from dropdown.

### Virre integration

Virre integration requires certificates to be installed to servers. Current certificates are installed using following commands.

```bash
cd /usr/local/share/ca-certificates/virre # Create folder, if it doesn't exist.
sudo touch virre_intermediate.crt
sudo touch virre_root.crt
sudo touch virre_server_certificate.crt
* Copy-paste content from the files provided to you to the files you just created.
sudo update-ca-certificates # This is the actual command that registers certificates.
```

### Backup database

Most important thing to remember when making a backup is to sanitize the data, when needed. Usually we need to take dump from the database only for the development/testing purposes so normally you should sanitize the data. We are using [Django sanitized dump](https://github.com/andersinno/django-sanitized-dump/#django-management-commands) for sanitizing data so check the most recent instructions from the vendor.

<strong>When running backup for the staging/testing/development purposes, you should exclude few tables to limit the size of the backup.</strong> So remember to add `--exclude-table-data 'public.auditlog_logentry' --exclude-table-data 'public.batchrun_jobrunlog*' --exclude-table-data 'public.django_q_task'` to `pg_dump` command.

```bash
pg_dump mvj_api_prod | gzip > mvj-api-prod_$(date +%Y%m%d%H%m).sql.gz
```

To restore dump run `psql -f mvj-api-prod-DATE_HERE.sql ${DATABASE_URL/postgis/postgres}`.

### Token authentication

For machine-to-machine integration Django REST Framework's token based authentication is in use. To create token for the user you need to run `python manage.py drf_create_token <username>` command. If you need to renew token, then you need to append `-r` option to the command. To make things secure robot user should not have password set (aka cannot log in with browser) and it should only have access to the certain API endpoint and nothing else.

From client perspective token is sent in HTTP headers (Authorization header) with Token keyword. As an example `Authorization: Token abcdefghijklmnopqrstuvwxyz1234567890`.

### Virus scanning

All uploaded files are scanned for viruses by using an external file scanning
service, currently ClamAV Antivirus API service on Platta. The app
`file_operations` is responsible for orchestrating the scans.

In models, file scanning can be added through `FileScanMixin`. In viewsets, file
downloads can be restricted to only safe files through `FileDownloadMixin` or
any other mixin that calls this mixin in their download method, such as
`FileMixin`.

See the following management commands how to batch process historical uploaded
files:
- `create_filescanstatus_for_missing_files`
- `enqueue_scan_for_pending`

### Generate email reports locally into files

Some reports are not generated in the UI, but emailed to the user instead. This is replaced in the local development environment by generating the emails in the local file system instead. There are example configurations for this in the `local_settings.py.template`.

To generate the email files, you must first start the qcluster:

```bash
python manage.py qcluster
```

Now the emails can be created as `.log` files in the given `EMAIL_FILE_PATH`. Change the file extension into `.eml` to open the email in an email application.
