#!/bin/bash

COMPOSE_FILE_LOC=docker/docker-compose.integration.yml
COMPOSE_PROJECT_NAME_ORIGINAL=listenbrainz_int

# Project name is sanitized by Compose, so we need to do the same thing.
# See https://github.com/docker/compose/issues/2119.
COMPOSE_PROJECT_NAME=$(echo $COMPOSE_PROJECT_NAME_ORIGINAL | awk '{print tolower($0)}' | sed 's/[^a-z0-9]*//g')
TEST_CONTAINER_NAME=listenbrainz
TEST_CONTAINER_REF="${COMPOSE_PROJECT_NAME}_${TEST_CONTAINER_NAME}_1"

if [[ ! -d "docker" ]]; then
    echo "This script must be run from the top level directory of the listenbrainz-server source."
    exit -1
fi

echo "Take down old containers"
docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME down

echo "Build current setup"
docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME build

echo "Running setup"
docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME run --rm listenbrainz dockerize -wait tcp://db:5432 -timeout 60s \
                  -wait tcp://influx:8086 -timeout 60s \
                bash -c "python manage.py init_db --create-db && python manage.py init_msb_db --create-db && python admin/influx/create_db.py"

echo "Bring containers up and run integration tests"
docker-compose -f docker/docker-compose.integration.yml -p $COMPOSE_PROJECT_NAME up
