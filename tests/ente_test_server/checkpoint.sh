#!/bin/bash

# Checkpoint the database
docker exec -e PGPASSWORD=pgpass -it $(docker ps --filter 'name=postgres' --format '{{.ID}}') /bin/bash -c "pg_dump -U pguser ente_db | sed -e 's/$//' > /state/db.sql"

# Checkpoint minio objects
docker exec -it $(docker ps --filter 'name=minio' --format '{{.ID}}') /bin/bash minio-checkpoint.sh
