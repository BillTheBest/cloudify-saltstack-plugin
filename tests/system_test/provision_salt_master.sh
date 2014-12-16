#!/bin/bash
set -o errexit
set -o xtrace

sudo add-apt-repository --yes ppa:saltstack/salt
sudo apt-get update
sudo apt-get install --yes --no-install-recommends salt-master salt-api python-cherrypy3

sudo service salt-master stop || true
sudo service salt-api stop || true


# salt master configuration
sudo mkdir -p /etc/salt

sudo tee /etc/salt/master <<EOF
log_level_logfile: info

rest_cherrypy:
    port: 8000
    disable_ssl: True
    webhook_disable_auth: True

external_auth:
    pam:
        vagrant:
            - .*
            - '@wheel'

file_roots:
    base:
        - /srv/salt
EOF


# highstate definition
sudo mkdir -p /srv/salt

sudo tee /srv/salt/top.sls <<EOF
base:
  'role:testfile':
    - match: grain
    - teststate
EOF

sudo tee /srv/salt/teststate.sls <<EOF
/home/vagrant/cfy-salt-plugin-testfile:
  file.managed:
    - user: vagrant
    - group: vagrant
    - mode: 644
    - contents: This is a salt test file, minions with 'testfile' role should have it.
EOF


sudo service salt-master start
sudo service salt-api start
