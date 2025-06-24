#!/bin/bash

set -e

# Check if this is an initContainer
if [[ ! -z "$IS_KUBERNETES_INIT_CONTAINER" ]]; then
    echo "Running in initialization container mode"
    # Run migrations in init container
    bash deploy/init-migrate.sh
    # Exit to not start uwsgi in initContainer
    exit 0
fi

# Start server
if [[ ! -z "$@" ]]; then
    "$@"
else
    uwsgi --ini deploy/uwsgi.ini
fi
