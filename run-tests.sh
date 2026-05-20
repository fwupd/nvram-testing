#!/usr/bin/bash
#
#

set -x

DIRS=( "$(ls -d -- */)" )
RES=()
FAILED=0

for I in "${!DIRS[@]}"; do
    DIR="${DIRS[I]%%/}"
    pushd "$DIR"
        # per-directory test prereqs
        ../nvram.py get_reqs "$@"
        ../nvram.py extract

        # test itself
        ../nvram.py run "$@"
        if [[ "$?" -eq 0 ]]; then
            RES+=( "PASS: ${DIR}" )
        else
            RES+=( "FAIL: ${DIR}" )
            ((FAILED++))
        fi
    popd

    printf "%s\n" "${RES[@]}"
    if [[ "${FAILED}" -gt 0 ]]; then
        exit 1
    else
        echo "all good!" >&2
    fi
done
