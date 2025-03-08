#!/bin/bash

docker exec -it $(docker ps --filter 'name=minio' --format '{{.ID}}') /bin/bash
