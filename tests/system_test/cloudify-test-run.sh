#!/bin/bash

set -e
set -x

cfy blueprints upload -b blp$1 -p /vagrant/blueprint.yaml
cfy deployments create -b blp$1 -d dpl$1
cfy executions start -d dpl$1 -w install -l
