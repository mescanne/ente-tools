#!/bin/sh

# Script used to prepare the minio instance that runs as part of the development
# Docker compose cluster.

# Dump data in the bucket
for bucket in b2-eu-cen wasabi-eu-central-2-v3 scw-eu-fr-v3; do
	mc cp -r h0/${bucket} /state
done

exit 0
