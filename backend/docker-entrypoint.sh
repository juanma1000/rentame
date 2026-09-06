#!/bin/sh
set -e

# Local/compose: migrate on every start (single instance, safe).
# Autoscaled environments (e.g. App Runner) should set RUN_MIGRATIONS=false
# and run `alembic upgrade head` as a separate one-off deploy step instead —
# otherwise N replicas race to migrate the same database concurrently.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade head
fi

exec "$@"
