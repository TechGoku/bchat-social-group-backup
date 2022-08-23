#!/bin/bash

if ! [ -f contrib/upgrade-tests/common.sh ]; then
    echo "Wrong path: run from top-level bsgs" >&2
    exit 1
fi

if [ -z "$BSGS_PGSQL" ]; then
    echo "Error: must specify pg url via BSGS_PGSQL env variable" >&2
    exit 1
fi

. contrib/upgrade-tests/common.sh

set -o errexit

# Extract the BSGS 0.3.0 postgresql test database:
if ! [ -f test-bsgs-pg-f6dd80c04b.tar.xz ]; then
    curl -sSOL https://oxen.rocks/bsgs-assets/test-bsgs-pg-f6dd80c04b.tar.xz
fi

tar xf test-bsgs-pg-f6dd80c04b.tar.xz

psql -f bsgstest.pgsql "$BSGS_PGSQL"

# Update the timestamps to be relatively current (so that files aren't expired)
psql "$BSGS_PGSQL" <<SQL
UPDATE files SET uploaded = uploaded - 1646082000 + extract(epoch from now()),
    expiry = expiry - 1646082000 + extract(epoch from now())
WHERE expiry IS NOT NULL
SQL

do_upgrades "$@"
