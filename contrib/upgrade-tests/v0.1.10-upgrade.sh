#!/bin/bash

if ! [ -f contrib/upgrade-tests/common.sh ]; then
    echo "Wrong path: run from top-level bsgs" >&2
    exit 1
fi

. contrib/upgrade-tests/common.sh

set -o errexit

for tag in "$@"; do
    if ! git rev-parse "$tag" >/dev/null; then
        echo "'$tag' doesn't look like a valid known git revision or tag!"
        exit 1
    fi
done

# Extract the BSGS 0.1.10 test database:
if ! [ -f test-bsgs-0-1-10.tar.xz ]; then
    curl -sSOL https://oxen.rocks/bsgs-assets/test-bsgs-0-1-10.tar.xz
fi

tar xf test-bsgs-0-1-10.tar.xz

# Update the timestamps to be relatively current (so that we are importing files that shouldn't be
# expired):
for roomdb in rooms/*.db; do
    sqlite3 $roomdb "update files set timestamp = timestamp - 1645500000 + cast(((julianday('now') - 2440587.5)*86400.0) AS INTEGER)"
done

bsgs_key_conv=1
bsgs_fix_updates_count=1
bsgs_need_initialize=1
do_upgrades "$@"
