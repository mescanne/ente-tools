#!/bin/bash

cd "$(dirname $0)"

export INITSQL=""

docker compose down --remove-orphans --volumes
