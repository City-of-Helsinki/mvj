#!/bin/bash
set -e

echo "Entrypoint executing with args: $@"


start_api() {
    # Check if this is an initContainer
    if [[ ! -z "$IS_KUBERNETES_INIT_CONTAINER" ]]; then
        echo "Running in initialization container mode"
        # Run migrations in init container
        bash deploy/init-migrate.sh
        # Update django permissions
        echo "Run: set_group_field_permissions"
        ./manage.py set_group_field_permissions
        echo "Run: set_group_model_permissions"
        ./manage.py set_group_model_permissions
        echo "Run: set_report_permissions"
        ./manage.py set_report_permissions
        echo "Finished setting permissions"
        # Exit to allow main container to start, and in order to not start uwsgi in initContainer
        exit 0
    fi

    echo "Starting uWSGI server"
    exec uwsgi --ini deploy/uwsgi.ini
}

case "$1" in
    batchrun)
        echo "Running batchrun scheduler"
        exec python ./manage.py batchrun_scheduler
        ;;

    qcluster)
        echo "Running qcluster"
        exec python ./manage.py qcluster
        ;;

    api)
        echo "Running api"
        start_api
        ;;

    *)
        echo "Unknown command: $1"
        echo "Usage: $0 {batchrun|qcluster|api}"
        echo "Running default command: api"
        start_api
        ;;
esac
