# mvj
City of Helsinki ground rent system

## Development

### Creating requirements

* Run `pip-compile requirements.in`
* Run `pip-compile requirements-dev.in`

### Updating requirements

* Run `pip-compile --upgrade requirements.in`
* Run `pip-compile --upgrade requirements-dev.in`

### Installing requirements

* Run `pip install -r requirements.txt`
* Run `pip install -r requirements-dev.txt`

### Database

To setup a database compatible with the default database settings:

Create user and database

    sudo -u postgres createuser -P -R -S mvj  # use password `mvj`
    sudo -u postgres createdb -O mvj mvj

Allow user to create test database

    sudo -u postgres psql -c "ALTER USER mvj CREATEDB;"

### Running development environment

* Set the `DEBUG` environment variable to `1`.
* Run `python manage.py migrate`
* Run `python manage.py runserver 0:8000`

## Running tests

* Run `py.test`.
