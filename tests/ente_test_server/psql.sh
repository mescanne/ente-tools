#!/bin/bash

cd "$(dirname $0)"

docker exec -e PGPASSWORD=pgpass -it $(docker ps --filter 'name=postgres' --format '{{.ID}}') psql -U pguser ente_db
