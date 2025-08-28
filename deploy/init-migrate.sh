#!/bin/bash

set -e

# Apply database migrations
if [[ "$APPLY_MIGRATIONS" = "1" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
else
    echo "Skipping migrations..."
fi