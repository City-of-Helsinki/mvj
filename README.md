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

    sudo -u postgres psql -d "mvj" -c "CREATE EXTENSION postgis;"

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

### Running development environment

* Enable debug `echo 'DEBUG=True' >> .env`
* Run `python manage.py migrate`
* Run `python manage.py runserver 0.0.0.0:8000`

## Running tests

* Run `py.test`
