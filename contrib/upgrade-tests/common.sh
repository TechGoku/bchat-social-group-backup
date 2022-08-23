
set -o errexit

if [ "$1" != "--delete-my-crap" ]; then
    echo "
Warning: this script removes current database, files, and settings, and so should never be run on a
live installation.

Run with argument --delete-my-crap if that sounds okay" >&2

    exit 1
fi

shift

if ! [ -d contrib/upgrade-tests ] || ! [ -e bsgs/__init__.py ]; then
    echo "You need to run this as ./contrib/upgrade-test.sh from the top-level bsgs directory" >&2
    exit 1
fi

export PYTHONPATH=.

rm -rf rooms database.db files key_x25519 x25519_{public,private}_key.pem

echo -e "[log]\nlevel = DEBUG" >bsgs.ini
if [ -n "$BSGS_PGSQL" ]; then
    echo -e "[db]\nurl = $BSGS_PGSQL" >>bsgs.ini
    for table in rooms users messages message_history pinned_messages files room_users \
        user_permission_overrides user_permission_futures user_ban_futures user_request_nonces \
        inbox room_import_hacks file_id_hacks; do
        echo "DROP TABLE IF EXISTS $table CASCADE;"
    done | psql "$BSGS_PGSQL"
else
    rm -f bsgs.db{,-shm,-wal}
fi

for tag in "$@"; do
    if ! git rev-parse "$tag" >/dev/null; then
        echo "'$tag' doesn't look like a valid known git revision or tag!"
        exit 1
    fi
done


do_upgrades() {
    tags=("$@" "$(git rev-parse HEAD)")
    for tag in "${tags[@]}"; do
        echo "Upgrading to $tag..."
        git -c advice.detachedHead=false checkout "$tag"

        # Use the dedicated --upgrade command if it has been added in this revision:
        if [ -e bsgs/__main__.py ] && grep -q '^ *"--upgrade",$' bsgs/__main__.py; then
            args=("--upgrade")
        else
            # Before it was added, any command would implicitly upgrade:
            args=("-L")
        fi

        if [ -n "$bsgs_need_initialize" ]; then
            bsgs_need_initialize=

            if [ -n "$bsgs_key_conv" ]; then
                python3 -mbsgs.key_convert

                echo "Checking key_x25519 for proper conversion"
                diff --color=always \
                    <(python3 -c 'f = open("key_x25519", "rb"); print(f.read().hex())') \
                    <(echo a0101f8bca7fa1cedf9620f5b80810b18f5b0f1acbb219640876be9d78a6195f)
            fi

            # In 0.2.0 and up until close to 0.3.0, just running any command-line commands will do the
            # database import and/or upgrade.  Starting in 0.3.0 you have to specify --initialize to make
            # this happen.
            if [ -e bsgs/__main__.py ] && grep -q '^ *"--initialize",$' bsgs/__main__.py; then
                if [ "${args[0]}" == "--upgrade" ]; then
                    # If we support the --upgrade flag then --initialize and --upgrade are exclusive:
                    args=("--initialize")
                else
                    args+=("--initialize")
                fi
            fi
        fi

        python3 -mbsgs "${args[@]}"

        if [ -n "$bsgs_fix_updates_count" ]; then
            # 0.2.0 had a bug in one of the room update triggers that would unnecessarily update
            # `message_sequence` (then named `updates`) on metadata updates, which the 0.1.x import
            # triggered when setting the image value.  This was fixed before v0.3.0, but if our
            # first tag imports via such a problematic version then we need to undo the increment so
            # that the final message_sequence value remains comparable to a version that imported
            # directly into a newer release.
            if sed -ne '/^CREATE TRIGGER room_metadata_update/,/^END;/p' bsgs/schema.sql* \
                | grep -q 'SET updates = updates + 1'; then
                sqlite3 bsgs.db 'UPDATE rooms SET updates = updates - 1 WHERE image IS NOT NULL'
            fi
            bsgs_fix_updates_count=
        fi
    done

    # This should exit cleanly to indicate no needed migrations (if it doesn't, i.e. we still
    # require migrations after doing a migration then Something Getting Wrong in migrations).
    python3 -mbsgs --check-upgrades

    # Run the cleanup job to make sure we have the proper rooms.active_users values
    python3 -c 'from bsgs.cleanup import cleanup; cleanup()'
}
