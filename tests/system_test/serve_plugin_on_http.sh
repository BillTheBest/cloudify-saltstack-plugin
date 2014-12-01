#!/bin/bash


SOURCE_DIR=../../
SOURCE_YAML=plugin.yaml
TARGET_DIR="/tmp/temp-saltstack-plugin-$$"
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
    rmdir -vp "${target_path}" 2>/dev/null
    _pids=()
}


netstat=`netstat -4tlNnp 2>/dev/null | grep -E "^tcp([[:space:]]+[[:digit:]]+){2}[[:space:]]([[:digit:]]+\.){3}[[:digit:]]:${PORT}.*LISTEN"`
[ -n "${netstat}" ] && {
    pids=`echo "$netstat" | awk '{print $7}' | cut -d/ -f1 | xargs`
    kill ${pids}
}


for s in HUP INT QUIT TERM; do
    trap '_cleanup' "${s}"
done


set -x
set -e


mkdir -p "${TARGET_DIR}"
if [ "${TARGET_DIR:0:1}" = / ]; then
    target_path="${TARGET_DIR}"
else
    target_path="`pwd`/${TARGET_DIR}"
fi

pushd "${SOURCE_DIR}"
cp -v "${SOURCE_YAML}" "${target_path}/${TARGET_YAML}"
zip -r "${target_path}/${TARGET_ZIP}" *
popd

pushd "${TARGET_DIR}"
python -m SimpleHTTPServer "${PORT}" & _pids=(${_pids[@]} $!)

# Support for older bash, sorry.
if [ ${BASH_VERSINFO[0]} -gt 4 \
        -o ${BASH_VERSINFO[0]} -eq 4 -a ${BASH_VERSINFO[1]} -ge 3 ]; then
    sleep "${TIMEOUT}" & _pids=(${_pids[@]} $!)
    wait -n && _cleanup
else
    set -x
    for (( i = 0; i < ${TIMEOUT}; ++i )); do
        sleep 1 || break
    done
    set +x
    [ ${i} -ge ${TIMEOUT} ] && _cleanup
fi
