#!/bin/bash

cd "$(dirname $0)"

if [ $# != 1 ]; then
	echo "Specify state to use. base is the typical starting state."
	exit 1
fi

export STATE="$1"

echo "Starting with state ${STATE}"

docker compose up -d --force-recreate

ENTE_PORT=$(docker ps --filter 'name=museum' --format '{{.Ports}}' | awk '{print $1}' | cut -f1 -d'-' | cut -f2 -d':')
echo "Ente URL: http://localhost:${ENTE_PORT}"
