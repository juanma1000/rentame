#!/bin/sh
# Runs once on first container start (docker-entrypoint-initdb.d convention).
# Creates a separate database for the test suite alongside the dev database,
# so integration tests never touch dev data.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE ${POSTGRES_DB}_test'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}_test')\gexec
EOSQL
