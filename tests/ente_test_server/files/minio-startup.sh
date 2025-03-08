#!/bin/sh

# Script used to prepare the minio instance that runs as part of the development
# Docker compose cluster.

/usr/bin/minio server /data --address ":3200" --console-address ":3201" &
MINIO_SERVER_PID=$1
trap "kill $MINIO_SERVER_PID; exit" 15

# Configure connection
while ! mc config host add h0 http://localhost:3200 test testtest
do
   echo "waiting for minio..."
   sleep 0.5
done

# Initialize data in the bucket
for bucket in b2-eu-cen wasabi-eu-central-2-v3 scw-eu-fr-v3; do
	mc mb -p h0/${bucket}
	test -d /state/${bucket} && mc cp -r /state/${bucket}/* h0/${bucket}
done

wait
