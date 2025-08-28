#!/bin/bash

set -e

# List of envvars to be used to create directories
DIRECTORY_VARS=(
    "LASKE_EXPORT_ROOT"
    "LASKE_PAYMENTS_IMPORT_LOCATION"
    "PRIVATE_FILES_LOCATION"
    "NLS_IMPORT_ROOT"
)

create_dir() {
    local var_name="$1"
    local dir_path="${!var_name}"

    if [ -z "$dir_path" ]; then
        echo "$var_name is not defined, skipping directory creation."
        return
    fi

    if [ -d "$dir_path" ]; then
        echo "Directory ($var_name) $dir_path already exists, skipping creation."
    else
        echo "Creating ($var_name) directory $dir_path"
        mkdir -p "$dir_path"
    fi
}

for var_name in "${DIRECTORY_VARS[@]}"; do
    create_dir "$var_name"
done
