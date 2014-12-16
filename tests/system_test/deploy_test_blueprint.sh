#!/bin/bash
set -o errexit

source /home/vagrant/cloudify/bin/activate
cd ~/cloudify

set -o xtrace

cfy blueprints upload -b blp$1 -p /vagrant/blueprint.yaml
cfy deployments create -b blp$1 -d dpl$1
cfy executions start -d dpl$1 -w install -l

set +o xtrace

if [ -f /home/vagrant/cfy-salt-plugin-testfile ]; then
    echo "Test passed successfully."
    exit 0
else
    echo "Test failed:" >/dev/stderr
    echo "Salt didn't create the file specified in teststate.sls." >/dev/stderr
    exit 1
fi
