#!/bin/bash
set -o errexit

# Runs the full system test. See README.md for details.

vagrant up salt-master
vagrant up --no-provision cfy-minion
./serve_plugin_on_http.sh &
vagrant provision cfy-minion
