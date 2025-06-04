#!/bin/bash

set -e

if [ -z "$SKIP_DATABASE_CHECK" -o "$SKIP_DATABASE_CHECK" = "0" ]; then
    until nc -z -v -w30 "$DATABASE_HOST" "$DATABASE_PORT"
    do
      echo "Waiting for postgres database connection..."
      sleep 1
    done
    echo "Database is up!"
fi


# Apply database migrations
if [[ "$APPLY_MIGRATIONS" = "1" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi


# Start server
if [[ ! -z "$@" ]]; then
    "$@"
else
    uwsgi --ini deploy/uwsgi.ini
fi
