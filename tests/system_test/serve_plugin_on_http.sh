#!/bin/bash


SOURCE_DIR=../../
SOURCE_YAML=plugin.yaml
TARGET_DIR=temp_dir
TARGET_YAML=plugin.yaml
TARGET_ZIP=plugin.zip
PORT=8001
TIMEOUT=150


function _sleep {
    python -c "import time; time.sleep($1)"
}

declare -a _pids
function _cleanup {
    set +e
    set +x
    for p in ${_pids[@]}; do
        for s in HUP INT TERM KILL; do
            ps -fp "${p}" 1>/dev/null 2>&1 && kill "-${s}" "${p}"
            ps -fp "${p}" 1>/dev/null 2>&1 || break
            _sleep 0.1
        done
    done
    set -x
    rm -v "${target_path}/${TARGET_YAML}" "${target_path}/${TARGET_ZIP}"
    rmdir -v "${target_path}"
    _pids=()
}

for s in HUP INT QUIT TERM; do
    trap '_cleanup' "${s}"
done


set -x
set -e


mkdir -p "${TARGET_DIR}"
target_path="`pwd`/${TARGET_DIR}"

pushd "${SOURCE_DIR}"
cp -v "${SOURCE_YAML}" "${target_path}/${TARGET_YAML}"
rm -v "${target_path}/${TARGET_ZIP}" || true
zip -r "${target_path}/${TARGET_ZIP}" *
popd

pushd "${TARGET_DIR}"
python -m SimpleHTTPServer "${PORT}" & _pids=(${_pids[@]} $!)
sleep "${TIMEOUT}" & _pids=(${_pids[@]} $!)
wait -n
_cleanup
