#!/bin/bash

set -e

# Apply database migrations.
# Defaults to 1 in the newer Platta templates in mvj-pipelines repository.
if [[ "$APPLY_MIGRATIONS" = "1" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
else
    echo "Skipping migrations..."
fi
