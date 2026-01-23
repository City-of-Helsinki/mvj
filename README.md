[![codecov](https://codecov.io/gh/City-of-Helsinki/mvj/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/mvj)

# mvj

City of Helsinki land lease system


## Local development setup

### Set up a devcontainer

Code editors (e.g. VSCode, Pycharm) that support devcontainer spec should be able to build and run your development environment from `.devcontainer`, either locally or remotely.
See: [https://containers.dev/](https://containers.dev/)

The devcontainer setup will build and run containers for the database and django.
Integrated to the editor you gain access to the shell within the django container, running code with debugger or run tests in debugging mode should work without much hassle.

1. Copy-paste the file `./devcontainer/docker-compose.env.template` as `./devcontainer/docker-compose.env`
2. Copy-paste the file `local_settings.py.template` as `local_settings.py`
3. Install some container runtime on your machine. For example: some Docker offering, or `colima` on macOS.
4. Install devcontainer extension in your IDE
5. Reopen the repository in devcontainer in your IDE. This creates the necessary containers.


### Database setup

Have an existing developer send you a sanitized development database dump,
and load it into your local database in the container.
If you use a devcontainer, you should have built the necessary containers before
the following steps.

See instructions "Database backup" in this README for commands to dump and load
the data.
You can find the local connection details e.g. in `.devcontainer/docker-compose.env.template`

Verify that the loading worked by connecting to the database with `psql`.
You can for example run the command `\dt` to see a list of imported tables.

At this point, you should be able to run the API locally with
`python manage.py runserver 0:8001`. If that works, data should be fine.

### Django admin user

Create an admin user for yourself with `manage.py`:

```shell
python manage.py createsuperuser
```

You can use this user to login to the Django admin page at
`http://<local API address>/admin`

### Regular MVJ user

1. Set up and run the MVJ frontend `mvj-ui`, and navigate to the front page to log in.
2. Log in with your email

If you have the permission to access the site, you will be logged in, but will
still see permission errors, which are expected.
Logging in for the first time creates a user for you in MVJ database, but you
need to add correct user groups for it:

1. Log in to admin interface
2. Navigate to `Users` listing
3. Find your generated user by searching with your email address, and edit it
4. In the groups section ("Ryhmät"), select all the `TEST <group name>` groups,
  and click the right arrow to add them to your user.
    * If you don't see any "TEST _" groups, run `python manage.py copy_groups_and_service_unit_mappings`
5. In service units section at the bottom of the page, select any group.
6. Save the user
7. Refresh the UI page. This time you should see data without errors.


## Django configuration

Environment variables are used to customize configuration in `mvj/settings.py`.
If you wish to override any settings, you can place them in `local_settings.py`
which is executed at the end of the `mvj/settings.py`.

If using a devcontainer, be wary of overlap in variable values between
`local_settings.py` and `docker-compose.env`.
Docker env is updated when you build the container, and local settings is read
on every restart of the Django app.

## Managing Python libraries

### Install pip-tools

If you don't use a devcontainer, install `pip-tools` to get `pip-compile` and `pip-sync`:

```shell
pip install --upgrade pip
pip install pip-tools
```

### Update Python requirements files

To update a single package:

```shell
pip-compile --upgrade-package <package name>
```

To update all packages:

```shell
pip-compile --upgrade requirements.in
pip-compile --upgrade requirements-dev.in
pip-compile --upgrade requirements-prod.in
```

If you need to pin a library version, use the `.in` files for your direct
dependencies, and `constraints.txt` for subdependencies.

### Update requirements.txt files from .in files

When you change the libraries in the`.in` files, regenerate the `.txt` files
with `pip-compile`:

```shell
pip-compile requirements.in
pip-compile requirements-dev.in
```

### Update your environment from requirements files

Install the requirements with `pip`:

```shell
pip install -r requirements.txt -r requirements-dev.txt
```

... or with `pip-sync`. Pip-sync will add, update, and **remove** packages to
ensure the environment matches the requirements file. This makes the environment
repeatable, but make sure you are in a virtual environment or container before
running this, or your global python requirements will be overridden, which might
break your system.

```shell
# Activate the venv if not using a devcontainer:
python3 venv/bin/activate

# Sync your environment with the requirements.
pip-sync requirements.txt requirements-dev.txt
```


## Database setup from scratch

!! This instruction is for setting up a database compatible with the default
database settings from scratch, without using a recent database dump.
This process has not been tested in a long while, so expect troubleshooting !!

Create a database user and the database:

```shell
sudo -u postgres createuser -P -R -S mvj
sudo -u postgres createdb -O mvj mvj-db
```

Enable the PostGIS extension:

```shell
sudo -u postgres psql -d "mvj" -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Allow the mvj user to create databases when running tests:

```shell
sudo -u postgres psql -d "mvj" -c "ALTER USER mvj CREATEDB;"
```

Tests also require that PostGIS extension is installed on the test database.
This can be achieved the easiest by adding PostGIS extension to the default
template which is then used when the test databases are created:

```shell
sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Run Django migrations:

```shell
python manage.py migrate
```

Load data from fixtures:

```shell
python manage.py loaddata */fixtures/*.json
```

Run the necessary install-time management commands. Might not be exhaustive:

```shell
python manage.py compilemessages
python manage.py set_report_permissions
python manage.py set_group_field_permissions
python manage.py set_group_model_permissions
python manage.py copy_groups_and_service_unit_mappings   # Only for non-prod environments.
```


## Running tests

Use your IDE's test runner capabilities, or run `pytest` from terminal.


## Update translation files

Generate empty keys for the new translation entries:

```shell
python manage.py app_makemessages --locale fi --locale sv
```

Write your translations in the new translation entries in `django.po` files...

... and then generate the locales again, so that app_makemessages can format
your translations in the .po files, avoiding automatic formatting changes later:

```shell
python manage.py app_makemessages --locale fi --locale sv
```

Finally, compile translations binaries for Django:

```shell
python manage.py compilemessages
```

## Management commands

Some management commands should be run regularly, some on new deployments, and
some only in specific circumstances.

The following list is not exhaustive. Check the latest list with `python manage.py`.

### Install time commands

#### `app_makemessages`

Generate `django.po` localization files based on the latest code.
Needs to to be run every time you change/add/remove translated text in code.
Then you write your translations to the newly generated keys in the `.po` files.

Afterwards, run the `compilemessages` command to generate translation binaries.

#### `compilemessages`

Compiles translation binaries from `django.po` files.
Needs to be run every time `.po` files are changed.

#### `set_report_permissions`

Sets permitted groups for each report type.

#### `set_group_model_permissions`

Sets the default model specific permissions (view, add, change, delete) to the pre-defined groups for the leasing models.

#### `set_group_field_permissions`

Sets field specific permissions (view, change) to the pre-defined groups.

#### `copy_groups_and_service_unit_mappings`

Creates copies of all user groups and service unit groups with prefix `TEST <groupname>`.
This is needed in non-prod environments for developers, because the original groups
are synced/wiped based on AD groups that are not in MVJ control.

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

_In production, should be run on the first day of every month_

Has a variant for single lease, for manual actions: `create_invoices_for_single_lease`

#### `send_invoices_to_laske`

Sends unsent invoices to Laske SAP for invoicing.

_In production, should be run every night_

#### `import_index`

Imports index from stat.fi.

_In production, should be run monthly after stat.fi update day_

#### `import_interest_rate`

Imports reference interest rates from the Bank of Finland.

_In production, should be run after the Bank of Finland releases new rates_

#### `index_rent_equalization`

Creates credit notes or invoices if index number has changed after the invoices are sent.

_In production, should be run once a year after the previous years index has been released_

#### `import_leasehold_transfers`

Imports leasehold transfers from National Land Survey of Finland (Maanmittauslaitos).

_In production, should be run every week_

#### `mvj_import`

Imports areas and usage distributions.

_In production, should be run daily_

#### `attach_areas`

Attaches imported areas to MVJ model instances.

_In production, should be run daily_

#### `generate_export_report_lease_statistic`

Generates Lease statistics report for Export API.

Can be generated in desired intervals, how often the report should need to be updated. For now daily.

#### `qcluster`

The asynchronous task runner in MVJ. Used for example for PDF and report generation,
sending scheduled emails, scanning files for viruses, scheduling sending auditlogs
to permanent storage etc.

Not a management command as such, but is started the exact same way with `manage.py`

#### `submit_unsent_entries`

A management command of `django-resilient-logger` used to push `django-auditlog`
auditlogs to permanent storage.


## Other useful information

### Resend Invoices

You can resend the failed invoices in [Django admin Invoices](https://mvj.dev.hel.ninja/admin/leasing/invoice/)
view by selecting the invoices and chosing Resend invoice action from dropdown.

### Token authentication

For machine-to-machine integration Django REST Framework's token based authentication is in use. To create token for the user you need to run `python manage.py drf_create_token <username>` command. If you need to renew token, then you need to append `-r` option to the command. To make things secure robot user should not have password set (aka cannot log in with browser) and it should only have access to the certain API endpoint and nothing else.

From client perspective token is sent in HTTP headers (Authorization header) with Token keyword. As an example `Authorization: Token abcdefghijklmnopqrstuvwxyz1234567890`.

### Virus scanning

All uploaded files are scanned for viruses by using an external file scanning
service. The app `file_operations` is responsible for orchestrating the scans.

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
### Database backup

Before doing extensive deployments, backup the database:

```bash
pg_dump --dbname <dbname> --username <username> --host <db address> --format custom --file mvj-ENVIRONMENT_$(date +%Y%m%d%H%m).dump
```

To restore the database from backup, run:

```bash
pg_restore --dbname <dbname> --username <username> --host <db address> --clean --if-exists mvj-ENVIRONMENT_DATETIME.dump
```


## Sanitized database dump

!! This instruction was written for the old on-premises server, and doesn't work
as-is in other environments !!

When taking a database dump from production to be used for development or testing
purposes, sensitive fields must be sanitized. We use
[Django sanitized dump](https://github.com/andersinno/django-sanitized-dump/#django-management-commands)
for sanitizing the data.

### 0. Activate virtual environment with development dependencies

Sanitizer requires some Python packages that are listed as development dependencies.

If the source environment already has development dependencies installed,
continue to next topic.

```bash
sudo su <api user>
cd
# <Here you should load the environment variables required by API user>

# Create the virtual environment, if it doesn't exist yet:
python -m venv venv-dev

# Activate the venv-dev environment
source venv-dev/bin/activate

# Install all dependencies, if not installed yet:
pip install -r <api directory>/requirements-dev.txt
pip install -r <api directory>/requirements.txt
```

### 1. Validate sanitizer configuration

Sanitizer configuration is specified in `.sanitizerconfig`.
First, validate if the current configuration is up to date with Django models:

```bash
cd <api user directory>
# <Here you should load the environment variables required by API user>
python manage.py validate_sanitizerconfig
```

This will tell you if any models or model fields are missing from the
configuration based on current state of the models.

### 2. Update sanitizer configuration

If you have any deficiencies in the configuration, update the configuration file.

Our custom sanitizer functions are specified in `sanitizers/mvj.py`.
The [library's own sanitizer functions](https://github.com/andersinno/python-database-sanitizer/tree/master/database_sanitizer/sanitizers) are also available.

`skip_rows` strategy can be used to entirely avoid dumping rows from a table
that contains data unnecessary for development purposes.
The table schema is still included in the dump

If you need lots of changes, you can fully reset the configuration file.
Afterwards, only stage the updates you need to version control, and avoid
setting row sanitizers to null if they specified a sanitization function before.

```bash
# Only run this if you need the reset
python manage.py init_sanitizer
```

### 3. Create sanitized dump

```bash
python manage.py create_sanitized_dump > mvj-sanitized-<ENVIRONMENT>_$(date +%Y%m%d%H%M).sql
```

Then copy the SQL file from source server to destination server, e.g. with `scp` tool.

### 4. Backup the destination database

```bash
python manage.py database_backup_before_load <db name> <db host> <db port> <db user>
```

### 5. Load the sanitized dump

Load the SQL dump with `psql`:

```bash
psql --username <db username> --dbname <db name> --host <db hostname> --port <db port> --file mvj-sanitized-ENVIRONMENT_DATETIME.sql > dump_loading.log
```

### 6. Restore environment-specific settings

```bash
python manage.py environment_specific_restore_after_database_load <db name> <db host> <db port> <db user>
```

### 7. Restore user access to MVJ

Sanitized dump will overwrite or drop existing users, including admin users.
Admin users were restored in previous step, but regular users will require more actions.

```bash
# Create TEST groups for non-AD users
python manage.py copy_groups_and_service_unit_mappings
```

On first login to MVJ, your regular user will be created.
After that, login to Django admin as your superuser and grant your regular user
at least:
- one group
- one service unit

### 8. Additional restoration tasks and cleanup

Some other environment-specific data might need to be restored, for daily
work to continue as before.
Review the generated backups and the new contents of the DB, and restore any
tables or their rows as you require.

When no longer needed, delete the backups.
