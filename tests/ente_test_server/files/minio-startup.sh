#!/bin/sh

echo "Starting Minio server..."
/usr/bin/minio server /data --address ":3200" --console-address ":3201" &
MINIO_SERVER_PID=$!
trap "echo 'Stopping Minio server...'; kill $MINIO_SERVER_PID; exit" TERM INT

echo "Configuring Minio alias..."
while ! mc alias set h0 http://localhost:3200 test testtest > /dev/null 2>&1
do
    echo "Waiting for Minio server to be ready..."
    sleep 0.5
done
echo "✅ Minio alias 'h0' configured."

# Initialize data in the buckets
for bucket in b2-eu-cen wasabi-eu-central-2-v3 scw-eu-fr-v3; do
    echo "Processing bucket: ${bucket}"

    # Create bucket using 'mc mb --ignore-existing'.
    mc mb --ignore-existing "h0/${bucket}"

    if [ -d "/state/${bucket}" ]; then
        echo "   -> Copying initial data to bucket: ${bucket}"
        mc cp --recursive "/state/${bucket}/" "h0/${bucket}"
    else
       echo "No initial data found for bucket: ${bucket} (skipping copy)"
    fi
done

echo "✅ Minio setup complete. Waiting for server process to terminate..."

# Wait for the Minio server process to finish
wait $MINIO_SERVER_PID
