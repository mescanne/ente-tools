#!/bin/bash

cd "$(dirname $0)"

export INITSQL="${INITSQL:-init.sql}"

echo "Starting with init sql ${INITSQL}"

docker compose up -d --force-recreate

echo -n "Minio port:             "
docker ps --filter 'name=minio' --format '{{.Ports}}' | awk '{print $2}' | cut -f1 -d'-'

echo -n "Museum (Ente API) port: "
docker ps --filter 'name=museum' --format '{{.Ports}}' | awk '{print $1}' | cut -f1 -d'-'

echo -n "Postgres port:          "
docker ps --filter 'name=postgres' --format '{{.Ports}}' | awk '{print $1}' | cut -f1 -d'-'
