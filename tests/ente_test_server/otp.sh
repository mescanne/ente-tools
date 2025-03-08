#!/bin/bash

docker logs $(docker ps --filter 'name=museum' --format '{{.ID}}') 2>&1 | grep 'Verification code:' | sed -e 's/^.*Verification code: //' | tail -n 1
