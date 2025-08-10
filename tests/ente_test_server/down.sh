#!/bin/bash

cd "$(dirname $0)"

export STATE=""

docker compose down --remove-orphans --volumes
