#!/bin/bash

cd "$(dirname $0)"

# Fetch the testing port port and URL
ENTE_PORT=$(docker ps --filter 'name=museum' --format '{{.Ports}}' | awk '{print $1}' | cut -f1 -d'-' | cut -f2 -d':')
ENTE_URL="http://localhost:${ENTE_PORT}"

# Download URL isn't the default, either
ENTE_DOWNLOAD_URL="${ENTE_URL}/files/download/"

# Dispatch
../../.venv/bin/ente-tool \
	--config test_config.toml \
	--database test_db.jsonl.gz \
	--api-url "${ENTE_URL}" \
	--api-account-url "${ENTE_URL}" \
	--api-download-url "${ENTE_DOWNLOAD_URL}" \
	--max-vers 0 \
	--sync-dir ./local \
	$*
