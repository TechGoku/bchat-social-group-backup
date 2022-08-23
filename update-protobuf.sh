#!/bin/bash

set -e

if ! [ -e "bsgs/__init__.py" ]; then
    echo "Error: must run this from the bchat_social_group root directory" >&2
    exit 1
fi

protos=(session.proto)

tmp=$(mktemp -d protobuf.XXXXXXXX)
cd $tmp
mkdir bsgs
for proto in "${protos[@]}"; do
    ln -s "../../bsgs/static/$proto" "bsgs/$proto"
done

protoc --python_out . bsgs/*.proto

for proto in "${protos[@]}"; do
    pb2_py="${proto/-/_}"
    pb2_py="bsgs/${pb2_py/.proto/}_pb2.py"
    if cmp -s $pb2_py ../$pb2_py; then
        rm -f $pb2_py
        echo "$pb2_py unchanged"
    else
        mv -f $pb2_py ../bsgs/
        echo "$pb2_py updated"
    fi
    rm bsgs/$proto
done

rmdir bsgs
cd ..
rmdir $tmp
