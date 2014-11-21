#!/bin/bash

SOURCE_DIR=saltstack-plugin
SOURCE_YAML=plugin.yaml
TARGET_DIR=tmp_dir
TARGET_YAML=plugin.yaml
TARGET_ZIP=plugin.zip
PORT=8001
TIMEOUT=150s

set -x

target_path="`pwd`/${TARGET_DIR}"
mkdir -p "${target_path}"

pushd "${SOURCE_DIR}"
cp "${SOURCE_YAML}" "${target_path}/${TARGET_YAML}"
rm "${target_path}/${TARGET_ZIP}"
zip -r "${target_path}/${TARGET_ZIP}" *
popd

pushd "${TARGET_DIR}"
timeout -s9 "${TIMEOUT}" python -m SimpleHTTPServer "${PORT}"
popd
