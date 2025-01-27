
# Ente Test Server

This is docker compose setup that creates an Ente test server that can
be automated with Python Test Containers.

## Test user

A well known test user is created in the [init.sql](sql/init.sql).

User:

Email:    ente-tools@test.com
Password: 32lj4h5iuhe

This user is an admin and is used for testing.

## Tools

### up.sh

Starts the docker compose environment from a the sql/init.sql. This initializes the test
user as admin and that's it.

### down.sh

Stops the docker compose environment and deletes all volumes. All data is lost.

### pg_dump.sh

Dumps the postgres database to stdout, allowing you to capture the state of the test
server completely.

### psql.sh

Allows you to enter the psql command of the postgres database.

### otp.sh

Retrieves the last OTP issued by the server from the museum logs. This allows you to
authenticate your email when it actually isn't sent.
