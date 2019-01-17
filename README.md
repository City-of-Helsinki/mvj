[![Build status](https://travis-ci.org/City-of-Helsinki/mvj.svg?branch=master)](https://travis-ci.org/City-of-Helsinki/mvj)
[![codecov](https://codecov.io/gh/City-of-Helsinki/mvj/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/mvj)

# mvj
City of Helsinki ground rent system

## Development

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

* Run `pip-compile requirements.in`
* Run `pip-compile requirements-dev.in`

### Updating Python requirements files

* Run `pip-compile --upgrade requirements.in`
* Run `pip-compile --upgrade requirements-dev.in`

### Installing Python requirements

* Run `pip install -r requirements.txt`
* For development also run `pip install -r requirements-dev.txt`

### Database

To setup a database compatible with the default database settings:

Create user and database

    sudo -u postgres createuser -P -R -S mvj  # use password `mvj`
    sudo -u postgres createdb -O mvj mvj

Enable PostGIS

    sudo -u postgres psql -d "mvj" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Allow the mvj user to create databases when running tests

    sudo -u postgres psql -c "ALTER USER mvj CREATEDB;"

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

* Enable debug `echo 'DEBUG=True' >> .env`
* Run `python manage.py migrate`
* Run `python manage.py loaddata */fixtures/*.json`
* Run `python manage.py runserver 0.0.0.0:8000`

## Running tests

* Run `pytest`


## Management commands

There are multiple management commands that are required to run. Either when first installing the software or regularly.


### Install time commands

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


### Development commands

No need to run.

#### `attach_areas`
#### `compare_rent_amounts`
#### `mvj_import`
#### `set_contact_cities_from_postcodes`
